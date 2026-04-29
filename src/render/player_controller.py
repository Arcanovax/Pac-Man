import math
from typing import Callable, Any

from ursina import (
    BoxCollider,
    Entity,
    Vec2,
    Vec3,
    camera,
    clamp,
    held_keys,
    mouse,
    raycast,
    scene,
    time,
    color
)

AXIS_X = 'x'
AXIS_Z = 'z'


class PlayerController(Entity):
    def __init__(
        self,
        speed: float = 10,
        collider_size: Vec3 = Vec3(0.99, 2, 0.99),
        eye_height: float = 1.6,
        fov: float = 100,
        mouse_sensitivity: Vec2 = Vec2(40, 40),
        skin_width: float = 0.04,
        mini_map=None,
        cheats_menu=None,
        maze_3d=None,
        config=None,
        pacgums: dict | None = None,
        hit_ghost: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.speed = speed
        self.gravity = 0
        self.collider_size = collider_size
        self.eye_height = eye_height
        self.fov = fov
        self.mouse_sensitivity = mouse_sensitivity
        self.skin_width = skin_width
        self.mini_map = mini_map
        self.pacgums = pacgums
        self.cheats_menu = cheats_menu
        self.maze_3d = maze_3d
        self.hit_ghost = hit_ghost

        self._breath_t = 0.0
        self._base_camera_y = self.eye_height
        self._current_breath_offset = 0.0

        self.position = mini_map.player_spawn
        self.lives = config.lives
        self.spawn_position = Vec3(
            self.position.x,
            self.position.y,
            self.position.z,
        )

        self.camera_pivot = Entity(parent=self, y=self.eye_height)
        camera.parent = self.camera_pivot
        camera.position = Vec3(0, 0, 0)
        camera.rotation = Vec3(0, 0, 0)
        camera.fov = self.fov

        self.collider = BoxCollider(
            self,
            center=Vec3(0, self.collider_size.y / 2, 0),
            size=self.collider_size,
        )

    def _handle_speed_cheat(self):
        if (self.cheats_menu.get_cheat("speed").state):
            self.speed = self.cheats_menu.get_cheat("speed").state

    def _handle_lives_cheat(self):
        if (self.cheats_menu.get_cheat("extra_lives").state):
            self.cheats_menu.get_cheat("extra_lives").state = False
            self.lives += 1

    def _axis_direction(self, axis: str, delta: float) -> Vec3:
        direction = Vec3(1, 0, 0) if axis == AXIS_X else Vec3(0, 0, 1)
        if delta < 0:
            return -direction
        return direction

    def _axis_half_width(self, axis: str) -> float:
        if axis == AXIS_X:
            return self.collider_size.x / 2
        return self.collider_size.z / 2

    def _ray_origins(self) -> tuple[Vec3, Vec3, Vec3]:
        return (
            self.world_position + Vec3(0, 0.2, 0),
            self.world_position + Vec3(0, self.collider_size.y * 0.5, 0),
            self.world_position + Vec3(0, self.collider_size.y - 0.2, 0),
        )

    def _axis_blocked(self, axis: str, delta: float) -> bool:
        if abs(delta) < 0.0001:
            return False

        direction = self._axis_direction(axis, delta)
        half_width = self._axis_half_width(axis)
        distance = half_width + abs(delta) + self.skin_width

        for origin in self._ray_origins():
            hit = raycast(
                origin,
                direction,
                distance=distance,
                ignore=(self,),
                traverse_target=scene,
            )
            if hit.hit:
                if self._handle_noclip(axis, delta):
                    return False

            if hit.hit and not getattr(hit.entity, 'is_trigger', False):
                return True

        return False

    def _handle_noclip(self, axis, delta):
        if (self.cheats_menu.get_cheat("no_clip").state):
            if axis == 'x':
                wall_limit = self.maze_3d.x * self.maze_3d.scale
                if 0 < self.position.x + delta < wall_limit:
                    return True
            elif axis == 'z':
                wall_limit = -self.maze_3d.y * self.maze_3d.scale
                if wall_limit < self.position.z + delta < 0:
                    return True

    def _move_axis(self, axis: str, delta: float) -> None:
        if self._axis_blocked(axis, delta):
            return

        if self.maze_3d and self._walls_limits(axis, delta):
            return

        setattr(self, axis, getattr(self, axis) + delta)

    def _walls_limits(self, axis: str, delta: float):
        next_pos = getattr(self.position, axis) + delta
        if axis == 'x':
            wall_limit = self.maze_3d.x * self.maze_3d.scale
            if next_pos < -1 or next_pos > wall_limit + 1:
                return True
        elif axis == 'z':
            wall_limit = -self.maze_3d.y * self.maze_3d.scale
            if next_pos < wall_limit - 1 or next_pos > 1:
                return True
        return False

    def _rotate_camera(self):
        if self.cheats_menu.menu.enabled is True:
            return

    def _mouse_look(self) -> None:
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x -= (
            mouse.velocity[1] * self.mouse_sensitivity[1]
        )
        self.camera_pivot.rotation_x = clamp(
            self.camera_pivot.rotation_x,
            -89,
            89,
        )

    def _movement_input(self) -> Vec3:
        return Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s'],
        )

    def _move_player(self, move_input: Vec3) -> bool:
        if move_input == Vec3(0, 0, 0):
            return False

        self._handle_speed_cheat()
        move_input = move_input.normalized() * self.speed * time.dt
        world_move = (self.right * move_input.x) + \
            (self.forward * move_input.z)

        self._move_axis(AXIS_X, world_move.x)
        self._move_axis(AXIS_Z, world_move.z)
        self._minimap_move_player()
        return True

    def update(self) -> None:
        self._mouse_look()
        is_moving = self._move_player(self._movement_input())

        self._rotate_camera()
        self._minimap_rotate_player()
        self._handle_pacgums_collisions()
        self._handle_lives_cheat()
        self._apply_breathing(is_moving)

    def _handle_wallhack(self, model: Any) -> None:
        is_actif = self.cheats_menu.get_cheat("wallhack").state
        model.always_on_top = is_actif
        if is_actif:
            model.color = color.red
        else:
            model.color = color.white

    def _is_inside_square(self, target_pos: Vec3, half_size: float) -> bool:
        return (
            self.position.x <= target_pos.x + half_size and
            self.position.x >= target_pos.x - half_size and
            self.position.z <= target_pos.z + half_size and
            self.position.z >= target_pos.z - half_size
        )

    def _handle_pacgums_collisions(self) -> None:
        if not self.pacgums:
            return

        for gum in self.pacgums.get('normal', []):
            if not gum.visible:
                continue
            self._handle_wallhack(gum.model)
            gum_pos = gum.model.position
            if self._is_inside_square(gum_pos, half_size=1):
                gum.hide()

        for gum in self.pacgums.get('super', []):
            if not gum.visible:
                continue
            gum_pos = gum.model.position
            self._handle_wallhack(gum.model)
            if (
                self.position.x <= gum_pos.x + 2 and
                self.position.x >= gum_pos.x - 2 and
                self.position.z <= gum_pos.z + 2 and
                self.position.z >= gum_pos.z - 2
            ):
                if self._is_inside_square(gum_pos, half_size=2):
                    gum.hide()

    def _minimap_move_player(self) -> None:
        self.mini_map.player.x = self.position.x
        self.mini_map.player.z = self.position.z

    def _minimap_rotate_player(self) -> None:
        self.mini_map.player.rotation_y += mouse.velocity[0] * 40

    def _apply_breathing(self, is_moving: bool) -> None:
        if is_moving:
            frequency = 16.0
            amplitude = 0.028
        else:
            frequency = 3.8
            amplitude = 0.008

        self._breath_t += time.dt * frequency
        target_offset = math.sin(self._breath_t) * amplitude
        self._current_breath_offset += (
            target_offset - self._current_breath_offset
        ) * min(1.0, time.dt * 12.0)
        self.camera_pivot.y = self._base_camera_y + self._current_breath_offset

    def reset_to_spawn(self) -> None:
        self.position = Vec3(
            self.spawn_position.x,
            self.spawn_position.y,
            self.spawn_position.z,
        )
        self.rotation = Vec3(0, 0, 0)
        self.camera_pivot.rotation_x = 0
        self._breath_t = 0.0
        self._current_breath_offset = 0.0
        self.camera_pivot.y = self._base_camera_y
        self._minimap_move_player()
        self.mini_map.player.rotation_y = 90
