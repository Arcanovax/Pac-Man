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
from ..parsing.model import ConfigModel
from ..ghosts.ghost import (
    STATE_EATEN,
    Blinky,
    Clyde,
    Inky,
    Pinky,
)
from ..ui.menu.hud import HUDTemplate
from ..ui.menu.cheat_menu import Cheat_menu
from ..ui.menu.cheat_menu import Cheat
from ..ui.menu.pause_menu import PauseMenuManager
from typing import Any, Callable


class MazeGameSession(Entity):  # type: ignore
    """Represents a single session of the 3D maze game.

    Manages the game loop, entities (player, ghosts, pacgums), scoring,
    and game states (pause, cheats, victory, game over).
    """

    def __init__(
        self,
        config: ConfigModel,
        on_game_over: Callable[[int], None] | None = None,
        on_victory: Callable[[int], None] | None = None,
        player_stats: Any = None
    ):
        """Initializes the game session.

        Args:
            config: The game configuration model.
            on_game_over: Callback function triggered upon game over.
            on_victory: Callback function triggered upon winning the level.
            player_stats: Player statistics with score, lives, and level.
        """
        super().__init__(parent=scene)
        self.config = config
        self.player_stats = player_stats
        level = player_stats.level
        self.size = config.level[level].width, config.level[level].height
        self.current_level = level
        self.nb_level = level + 1
        self.on_game_over = on_game_over
        self.on_victory = on_victory
        self.ended = False
        self.cheats: list[Cheat] = [
            Cheat("no_clip"),
            Cheat("speed", is_cursor=True),
            Cheat("wallhack"),
            Cheat("infinite_eat"),
            Cheat("extra_time", is_button=True),
            Cheat("extra_lives", is_button=True)
        ]
        self.score: int = int(player_stats.score)
        self.lives: int = int(player_stats.lives)
        self._show_cheats: bool = False
        self.power_mode_timer: float = 0.0
        self.invulnerable_timer: float = 1.5
        self.level_max_time: int = int(config.level[level].level_max_time)
        self.pause_manager: PauseMenuManager | None = None
        self.is_paused: bool = False
        self._cheat_unlock_sequence = (
            "up arrow",
            "up arrow",
            "down arrow",
            "down arrow",
            "left arrow",
            "right arrow",
            "left arrow",
            "right arrow",
        )
        self._cheat_input_buffer: list[str] = []

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
        """Build the maze, UI, player and ghost entities for the session."""
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
            self.size,
            self.current_level
        )

        self._normal_left = sum(
            1 for gum in self.pacgums.pacgums.get("normal", []) if gum.visible
        )
        self._super_left = sum(
            1 for gum in self.pacgums.pacgums.get("super", []) if gum.visible
        )

        self.cheats_menu = Cheat_menu(on_exit=self._close_cheat_menu)
        for i, cheat in enumerate(self.cheats):
            self.cheats_menu.add_cheat(cheat, i)
        self.cheats_menu.hide()

        self.player = PlayerController(
            speed=10,
            collider_size=Vec3(2.0, 2, 2.0),
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

    def _toogle_cheat_menu(self) -> None:
        """Toggle the cheat overlay and freeze or resume gameplay."""
        if self._show_cheats:
            self._close_cheat_menu()
        else:
            self._show_cheats = True
            self.cheats_menu.show()
            self._set_cheat_freeze(True)

    def _close_cheat_menu(self) -> None:
        """Close the cheat overlay and restore gameplay state."""
        if not self._show_cheats:
            return
        self._show_cheats = False
        self.cheats_menu.hide()
        self._set_cheat_freeze(False)

    def _set_cheat_freeze(self, frozen: bool) -> None:
        """Pause or resume active gameplay while the cheat menu is open."""
        if self.ended:
            return

        if frozen:
            self.player.enabled = False
            self.hud.countdown = False
            for ghost in self.ghosts:
                ghost.enabled = False
            return

        if self.is_paused:
            return

        self.player.enabled = True
        self.hud.countdown = True
        for ghost in self.ghosts:
            ghost.enabled = True

    def _track_cheat_sequence(self, key: str) -> bool:
        """Detect the unlock sequence for the cheat menu.

        Returns True when the sequence has just been completed.
        """
        if key not in ("up arrow", "down arrow", "left arrow", "right arrow"):
            return False

        self._cheat_input_buffer.append(key)
        max_len = len(self._cheat_unlock_sequence)
        if len(self._cheat_input_buffer) > max_len:
            self._cheat_input_buffer = self._cheat_input_buffer[-max_len:]

        if tuple(self._cheat_input_buffer) == self._cheat_unlock_sequence:
            self._cheat_input_buffer.clear()
            self._toogle_cheat_menu()
            return True

        return False

    def _toggle_pause_menu(self) -> None:
        """Open or close the pause overlay."""
        if self.ended:
            return

        if self.is_paused:
            self._resume_game()
        else:
            self._pause_game()

    def _pause_game(self) -> None:
        """Freeze gameplay and show the pause menu."""
        self.is_paused = True

        if self._show_cheats:
            self._toogle_cheat_menu()

        self.player.enabled = False

        for ghost in self.ghosts:
            ghost.enabled = False

        def on_resume() -> None:
            self._resume_game()

        def on_quit() -> None:
            self.ended = True
            self._freeze_gameplay()
            mouse.locked = False
            if self.on_game_over is not None:
                self.on_game_over(self.score)

        self.pause_manager = PauseMenuManager(None)
        self.pause_manager.show(on_resume, on_quit)

    def _resume_game(self) -> None:
        """Resume gameplay after a pause."""
        self.is_paused = False

        self.player.enabled = True

        for ghost in self.ghosts:
            ghost.enabled = True

        if self.pause_manager:
            self.pause_manager.hide()
            self.pause_manager = None

    def _build_hud(self) -> None:
        """Create the HUD with score, lives and countdown widgets."""
        self.hud = HUDTemplate(
            score=0,
            lives=self.lives,
            level=self.nb_level,
            remaining_time=float(self.level_max_time),
            countdown=True,
            on_time_finished=self._time_up,
        )

    def _time_up(self) -> None:
        """Handle the end of the countdown timer."""
        if self.ended:
            return
        self.ended = True
        self._freeze_gameplay()
        mouse.locked = False
        if self.on_game_over is not None:
            self.on_game_over(self.score)

    def _freeze_gameplay(self) -> None:
        """Disable active entities and persist the final stats."""
        self.player.enabled = False
        self.hud.countdown = False
        self.player_stats.update("score", self.score)
        self.player_stats.update("level", self.nb_level)
        self.player_stats.update("lives", self.lives)

        for ghost in self.ghosts:
            ghost.enabled = False

        for entity in scene.entities:
            if entity not in (camera, camera.ui):
                destroy(entity)

    def _activate_power_mode(self, duration: float = 8.0) -> None:
        """Activate the frightened state after a super pacgum."""
        self.power_mode_timer = max(self.power_mode_timer, float(duration))
        for ghost in self.ghosts:
            ghost.set_frightened(duration)

    def _handle_time_cheat(self) -> None:
        """Consume one time cheat charge and add time to the HUD."""
        time_cheat = self.cheats_menu.get_cheat("extra_time")
        if time_cheat is None or time_cheat.state <= 0:
            return

        time_cheat.state -= 1
        self.hud.add_time(15)

    def _is_infinite_eat_active(self) -> bool:
        """Return True when the player can eat ghosts endlessly."""
        cheat = self.cheats_menu.get_cheat("infinite_eat")
        return bool(cheat and cheat.state)

    def _distance_xz(self, lhs: Vec3, rhs: Vec3) -> float:
        """Return the horizontal distance between two 3D positions."""
        delta = lhs - rhs
        return float(((delta.x ** 2) + (delta.z ** 2)) ** 0.5)

    def _world_to_grid(self, world_pos: Vec3) -> tuple[int, int]:
        """Convert a world-space position to maze grid coordinates."""
        return (
            int(round(world_pos.x / self.maze_3d.scale)),
            int(round(world_pos.z / self.maze_3d.scale)),
        )

    def _respawn_positions(self) -> None:
        """Reset the player and ghosts to their spawn locations."""
        self.player.reset_to_spawn()
        for ghost in self.ghosts:
            ghost.reset_to_spawn()
        self.power_mode_timer = 0.0
        self.invulnerable_timer = 1.8

    def _on_player_hit(self) -> None:
        """Handle the player taking a hit from a non-frightened ghost."""
        if self._is_infinite_eat_active():
            return

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
        """Resolve collisions between the player and visible ghosts."""
        if self.invulnerable_timer > 0:
            return

        infinite_eat_active = self._is_infinite_eat_active()
        power_mode_active = self.power_mode_timer > 0 or infinite_eat_active

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

            if power_mode_active:
                ghost.on_eaten(respawn_delay=3.0)
                self.score += int(self.config.points_per_ghost)
                self.hud.set_score(self.score)
            else:
                self._on_player_hit()
            break

    def _sync_lives(self) -> None:
        """Keep HUD and player life counters aligned."""
        if self.player.lives != self.lives:
            self.lives = max(0, int(self.player.lives))

        self.player.lives = self.lives
        self.hud.set_lives(self.lives)

    def _sync_score(self) -> None:
        """Update the score from collected pacgums and victory state."""
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

    def update(self) -> None:
        """Main update loop called each frame.

        Handles movement processing, entity collisions, logic flow,
        timers, and UI synchronization.
        """
        if self.ended:
            return

        if self.is_paused or self._show_cheats:
            return

        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(
                0.0,
                self.invulnerable_timer - time.dt,
            )

        if self.power_mode_timer > 0:
            self.power_mode_timer = max(0.0, self.power_mode_timer - time.dt)

        self._handle_time_cheat()

        self.blinky.update_ai(self.blinky)
        self.pinky.update_ai(self.blinky)
        self.inky.update_ai(self.blinky)
        self.clyde.update_ai(self.blinky)
        self.mini_map.update_ghosts()

        self._check_ghost_collisions()
        self._sync_score()
        self._sync_lives()

    def close(self) -> None:
        """Cleans up the game session.

        Destroys all visual and sound entities, pacgums,
        and releases the mouse lock correctly.
        """
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

    def input(self, key: str) -> None:
        """Handles input events from the Ursina engine.

        Args:
            key: The string name of the key pressed.
        """
        if key == "escape":
            self._toggle_pause_menu()
            return

        if self.ended or self.is_paused:
            return

        self._track_cheat_sequence(key)


def run_main_maze(
    config: ConfigModel,
    on_game_over: Callable[[int], None] | None = None,
    on_victory: Callable[[int], None] | None = None,
    app: Ursina | None = None,
    player_stats: Any = None
) -> MazeGameSession:
    """Instantiates and begins a maze game session.

    Args:
        config: The game configuration constraints.
        on_game_over: Callback function for a game over event.
        on_victory: Callback function for a win event.
        app: Optional reference to an already existing Ursina instance.
        player_stats: Stats representing current player state.

    Returns:
        The running MazeGameSession entity object.
    """
    local_app = app
    if local_app is None:
        local_app = Ursina()

    session = MazeGameSession(
        config=config,
        on_game_over=on_game_over,
        on_victory=on_victory,
        player_stats=player_stats
    )

    if app is None:
        local_app.run()

    return session
