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
    camera
)
from .maze_3d import Maze_3d
from .minimap import MiniMap
from .player_controller import PlayerController
from .pacgums import Pacgums_Manager
from ..ui.menu.hud import HUDTemplate


class MazeGameSession(Entity):
    def __init__(
        self,
        config,
        on_game_over=None,
        on_victory=None,
    ):
        super().__init__(parent=scene)
        self.config = config
        self.on_game_over = on_game_over
        self.on_victory = on_victory
        self.ended = False
        self.score = 0
<<<<<<< HEAD
=======
        self._destroyables: list[Entity] = []
        self.cheats = {
            "no_clip": False,
            "speed": False
        }
>>>>>>> dc40e28 (cheat)

        self._build_world()
        self._build_hud()
        self._sync_score()

    def _build_world(self) -> None:
        size = (self.config.width, self.config.height)
        maze_gen = MazeGenerator(
            size=size,
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

        self.mini_map = MiniMap(self.maze_3d, size, 0.4)
        self._destroyables.append(self.mini_map)

        self.pacgums = Pacgums_Manager(
            scale_maze,
            self.config,
            self.maze_3d.pacgums_zone,
            self.mini_map,
        )

        self._normal_left = sum(
            1 for gum in self.pacgums.pacgums.get("normal", []) if gum.visible
        )
        self._super_left = sum(
            1 for gum in self.pacgums.pacgums.get("super", []) if gum.visible
        )



        self.player = PlayerController(
            speed=10,
            collider_size=Vec3(0.34, 2, 0.34),
            eye_height=2.0,
            fov=90,
            mini_map=self.mini_map,
            pacgums=self.pacgums.pacgums,
            cheats=self.cheats,
            maze_3d=self.maze_3d
        )

    def _build_hud(self) -> None:
        self.hud = HUDTemplate(
            score=0,
            lives=self.config.lives,
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
        self.input_handler.enabled = False
        self.hud.countdown = False

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
        self._sync_score()

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


def run_main_maze(
    config,
    on_game_over=None,
    on_victory=None,
    app: Ursina | None = None,
):
    local_app = app
    if local_app is None:
        local_app = Ursina()

    session = MazeGameSession(
        config=config,
        on_game_over=on_game_over,
        on_victory=on_victory,
    )

    if app is None:
        local_app.run()

    return session
