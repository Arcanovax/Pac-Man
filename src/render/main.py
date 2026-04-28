from mazegenerator import MazeGenerator
from ursina import (
    AmbientLight,
    DirectionalLight,
    Entity,
    Sky,
    Ursina,
    Vec3,
    color,
    destroy,
    mouse,
    scene,
    camera,
    time,
)
from .maze_3d import Maze_3d
from .minimap import MiniMap
from .player_controller import PlayerController
from .pacgums import Pacgums_Manager
from ..ghosts.ghost import (
    STATE_EATEN,
    STATE_FRIGHTENED,
    Blinky,
    Clyde,
    Inky,
    Pinky,
)
from ..ui.menu.hud import HUDTemplate
from ..ui.menu.cheat_menu import Cheat_menu
from ..ui.menu.cheat_menu import Cheat


class MazeGameSession(Entity):
    def __init__(
        self,
        config,
        on_game_over=None,
        on_victory=None,
        level=0
    ):
        super().__init__(parent=scene)
        self.config = config
        self.size = config.level[level].width, config.level[level].height
        self.on_game_over = on_game_over
        self.on_victory = on_victory
        self.ended = False
        self.score = 0
        self.cheats = [
            Cheat("no_clip"),
            Cheat("speed", is_cursor=True),
            Cheat("wallhack"),
            Cheat("extra_lives", is_button=True)
        ]

        self._show_cheats = False
        self.lives = int(self.config.lives)
        self.power_mode_timer = 0.0
        self.invulnerable_timer = 1.5

        self._build_world()
        self._build_hud()
        self._sync_score()

    def _closest_cell(
        self,
        target: tuple[int, int],
        cells: set[tuple[int, int]],
    ) -> tuple[int, int]:
        if target in cells:
            return target
        return min(
            cells,
            key=lambda cell: (
                abs(cell[0] - target[0]) +
                abs(cell[1] - target[1])
            ),
        )

    def _corner_spawn_cells(
        self,
        cells: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        raw_corners = [
            (0, 0),
            (0, -self.size[0] + 1),
            (self.size[0] - 1, 0),
            (self.size[1] - 1, -self.size[0] + 1),
        ]

        chosen: list[tuple[int, int]] = []
        used: set[tuple[int, int]] = set()
        for corner in raw_corners:
            cell = self._closest_cell(corner, cells)
            if cell in used:
                alternatives = sorted(
                    cells,
                    key=lambda item: (
                        abs(item[0] - corner[0]) +
                        abs(item[1] - corner[1])
                    ),
                )
                for candidate in alternatives:
                    if candidate not in used:
                        cell = candidate
                        break
            chosen.append(cell)
            used.add(cell)
        return chosen

    def _build_world(self) -> None:
        maze_gen = MazeGenerator(
            size=self.size,
            perfect=False,
            seed=self.config.seed,
        )
        maze = maze_gen.maze

        self.sky = Sky()

        mouse.locked = True

        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(1, -1, -1))

        self.ambient = AmbientLight(color=color.rgba32(100, 100, 100, 255))

        scale_maze = 4
        self.maze_3d = Maze_3d(maze, scale_maze)
        self.walkable_cells = set(self.maze_3d.pacgums_zone)

        self.mini_map = MiniMap(self.maze_3d, 0.4)

        self.pacgums = Pacgums_Manager(
            scale_maze,
            self.config,
            list(self.maze_3d.pacgums_zone),
            self.mini_map,
            self.size
        )

        self._normal_left = sum(
            1 for gum in self.pacgums.pacgums.get("normal", []) if gum.visible
        )
        self._super_left = sum(
            1 for gum in self.pacgums.pacgums.get("super", []) if gum.visible
        )

        self.cheats_menu = Cheat_menu()
        for i, cheat in enumerate(self.cheats):
            self.cheats_menu.add_cheat(cheat, i)
        self.cheats_menu.hide()

        self.player = PlayerController(
            speed=10,
            collider_size=Vec3(0.34, 2, 0.34),
            eye_height=2.0,
            fov=90,
            mini_map=self.mini_map,
            pacgums=self.pacgums.pacgums,
            cheats_menu=self.cheats_menu,
            maze_3d=self.maze_3d,
            config=self.config,
            hit_ghost=self._on_player_hit,
        )
        self.player.lives = self.lives

        spawn_cells = self._corner_spawn_cells(self.walkable_cells)

        self.blinky = Blinky(
            spawn_coords=spawn_cells[0],
            tile_size=scale_maze,
            walkable_cells=self.walkable_cells,
            maze_grid=maze,
            scatter_target=spawn_cells[0],
            player=self.player,
        )
        self.pinky = Pinky(
            spawn_coords=spawn_cells[1],
            tile_size=scale_maze,
            walkable_cells=self.walkable_cells,
            maze_grid=maze,
            scatter_target=spawn_cells[1],
            player=self.player,
        )
        self.inky = Inky(
            spawn_coords=spawn_cells[2],
            tile_size=scale_maze,
            walkable_cells=self.walkable_cells,
            maze_grid=maze,
            scatter_target=spawn_cells[2],
            player=self.player,
        )
        self.clyde = Clyde(
            spawn_coords=spawn_cells[3],
            tile_size=scale_maze,
            walkable_cells=self.walkable_cells,
            maze_grid=maze,
            scatter_target=spawn_cells[3],
            player=self.player,
        )
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]
        self.mini_map.attach_ghosts(self.ghosts)

    def _toogle_cheat_menu(self):
        if self._show_cheats:
            self._show_cheats = False
            self.cheats_menu.hide()
        else:
            self._show_cheats = True
            self.cheats_menu.show()

    def _build_hud(self) -> None:
        self.hud = HUDTemplate(
            score=0,
            lives=self.lives,
            level=1,
            remaining_time=float(self.config.level_max_time),
            countdown=True,
            on_time_finished=self._time_up,
        )

    def _time_up(self) -> None:
        if self.ended:
            return
        self.ended = True
        self._freeze_gameplay()
        mouse.locked = False
        if self.on_game_over is not None:
            self.on_game_over(self.score)

    def _freeze_gameplay(self) -> None:
        self.player.enabled = False
        self.hud.countdown = False

        for ghost in self.ghosts:
            ghost.enabled = False

        for entity in scene.entities:
            if entity not in (camera, camera.ui):
                destroy(entity)

    def _activate_power_mode(self, duration: float = 8.0) -> None:
        self.power_mode_timer = max(self.power_mode_timer, float(duration))
        for ghost in self.ghosts:
            ghost.set_frightened(duration)

    def _distance_xz(self, lhs: Vec3, rhs: Vec3) -> float:
        delta = lhs - rhs
        return ((delta.x ** 2) + (delta.z ** 2)) ** 0.5

    def _world_to_grid(self, world_pos: Vec3) -> tuple[int, int]:
        return (
            int(round(world_pos.x / self.maze_3d.scale)),
            int(round(world_pos.z / self.maze_3d.scale)),
        )

    def _respawn_positions(self) -> None:
        self.player.reset_to_spawn()
        for ghost in self.ghosts:
            ghost.reset_to_spawn()
        self.power_mode_timer = 0.0
        self.invulnerable_timer = 1.8

    def _on_player_hit(self) -> None:
        if self.ended or self.invulnerable_timer > 0:
            return

        self.lives -= 1
        self.player.lives = self.lives
        self.hud.set_lives(self.lives)

        if self.lives <= 0:
            self.ended = True
            self._freeze_gameplay()
            mouse.locked = False
            if self.on_game_over is not None:
                self.on_game_over(self.score)
            return

        self._respawn_positions()

    def _check_ghost_collisions(self) -> None:
        if self.invulnerable_timer > 0:
            return

        player_cell = self._world_to_grid(self.player.position)

        for ghost in self.ghosts:
            if ghost.state == STATE_EATEN or not ghost.visible:
                continue

            ghost_cell = self._world_to_grid(ghost.position)
            in_same_cell = ghost_cell == player_cell
            close_in_world = (
                self._distance_xz(self.player.position, ghost.position) <= 1.6
            )

            if not in_same_cell and not close_in_world:
                continue

            if self.power_mode_timer > 0 and ghost.state == STATE_FRIGHTENED:
                ghost.on_eaten(respawn_delay=3.0)
                self.score += int(self.config.points_per_ghost)
                self.hud.set_score(self.score)
            else:
                self._on_player_hit()
            break

    def _sync_lives(self):
        if self.player.lives != self.lives:
            self.lives = max(0, int(self.player.lives))

        self.player.lives = self.lives
        self.hud.set_lives(self.lives)

    def _sync_score(self) -> None:
        normal_left = sum(
            1 for gum in self.pacgums.pacgums.get("normal", []) if gum.visible
        )
        super_left = sum(
            1 for gum in self.pacgums.pacgums.get("super", []) if gum.visible
        )

        eaten_normal = self._normal_left - normal_left
        eaten_super = self._super_left - super_left

        if eaten_normal > 0:
            self.score += eaten_normal * int(self.config.points_per_pacgum)
        if eaten_super > 0:
            self.score += (
                eaten_super * int(self.config.points_per_super_pacgum)
            )
            self._activate_power_mode(duration=8.0)

        self._normal_left = normal_left
        self._super_left = super_left
        self.hud.set_score(self.score)

        if (self._normal_left + self._super_left) == 0 and not self.ended:
            self.ended = True
            self._freeze_gameplay()
            mouse.locked = False
            if self.on_victory is not None:
                self.on_victory(self.score)

    def update(self):
        if self.ended:
            return

        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(
                0.0,
                self.invulnerable_timer - time.dt,
            )

        if self.power_mode_timer > 0:
            self.power_mode_timer = max(0.0, self.power_mode_timer - time.dt)

        self.blinky.update_ai(self.blinky)
        self.pinky.update_ai(self.blinky)
        self.inky.update_ai(self.blinky)
        self.clyde.update_ai(self.blinky)
        self.mini_map.update_ghosts()

        self._check_ghost_collisions()
        self._sync_score()
        self._sync_lives()

    def close(self) -> None:
        mouse.locked = False

        for gum in self.pacgums.pacgums.get("normal", []):
            destroy(gum.model)
            destroy(gum.sprite)
        for gum in self.pacgums.pacgums.get("super", []):
            destroy(gum.model)
            destroy(gum.sprite)

        for entity in scene.entities:
            if entity not in (camera, camera.ui):
                destroy(entity)

        destroy(self)

    def input(self, key):
        if key == "escape":
            self._toogle_cheat_menu()


def run_main_maze(
    config,
    on_game_over=None,
    on_victory=None,
    app: Ursina | None = None,
    level=0
):
    local_app = app
    if local_app is None:
        local_app = Ursina()

    session = MazeGameSession(
        config=config,
        on_game_over=on_game_over,
        on_victory=on_victory,
        level=level
    )

    if app is None:
        local_app.run()

    return session
