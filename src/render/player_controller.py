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


class PlayerController(Entity):  # type: ignore
    """First-person player controller used in the 3D maze.

    Handles movement, mouse look, collision detection with raycasts,
    cheats integration, breathing camera effect and minimap synchronization.
    """
    def __init__(
        self,
        speed: float = 10,
        collider_size: Vec3 = Vec3(0.99, 2, 0.99),
        eye_height: float = 1.6,
        fov: float = 100,
        mouse_sensitivity: Vec2 = Vec2(40, 40),
        skin_width: float = 0.04,
        mini_map: Any = None,
        cheats_menu: Any = None,
        maze_3d: Any = None,
        config: Any = None,
        pacgums: dict[str, Any] | None = None,
        hit_ghost: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the player controller and related camera setup.

        Args mirror constructor arguments for configuration and external
        components like `mini_map`, `cheats_menu` and `maze_3d`.
        """
        super().__init__()
        self.speed = speed
        self.gravity = 0
        self.collider_size = collider_size
        self.eye_height = eye_height
        config_mouse_sensitivity = getattr(config, "mouse_sensitivity", None)
        if config_mouse_sensitivity is not None:
            mouse_sensitivity = Vec2(
                float(config_mouse_sensitivity),
                float(config_mouse_sensitivity),
            )

        self.fov = float(getattr(config, "fov", fov))
        self.mouse_sensitivity = mouse_sensitivity
        self.breathing_strength = float(
            getattr(config, "breathing_strength", 1.0)
        )
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

    def _handle_speed_cheat(self) -> None:
        """Apply a developer 'speed' cheat by overriding movement speed."""
        if (self.cheats_menu.get_cheat("speed").state):
            self.speed = self.cheats_menu.get_cheat("speed").state

    def _handle_lives_cheat(self) -> None:
        """Consume a single 'extra_lives' cheat to increment player lives."""
        extra_lives_cheat = self.cheats_menu.get_cheat("extra_lives")
        if extra_lives_cheat.state > 0:
            extra_lives_cheat.state -= 1
            self.lives += 1

    def _axis_direction(self, axis: str, delta: float) -> Vec3:
        """Return a unit vector along the requested axis for movement checks.

        Negative `delta` yields the opposite direction.
        """
        direction = Vec3(1, 0, 0) if axis == AXIS_X else Vec3(0, 0, 1)
        if delta < 0:
            return -direction
        return direction

    def _axis_half_width(self, axis: str) -> Any:
        """Return half the collider width along the given axis."""
        if axis == AXIS_X:
            return self.collider_size.x / 2
        return self.collider_size.z / 2

    def _ray_origins(self) -> tuple[Vec3, Vec3, Vec3]:
        """Return three ray origin positions from bottom to top of the body."""
        return (
            self.world_position + Vec3(0, 0.2, 0),
            self.world_position + Vec3(0, self.collider_size.y * 0.5, 0),
            self.world_position + Vec3(0, self.collider_size.y - 0.2, 0),
        )

    def _axis_blocked(self, axis: str, delta: float) -> bool:
        """Return True if movement along axis by delta is blocked by a wall.

        Uses multiple raycasts from the player's body to detect collisions
        and respects noclip cheats and trigger colliders.
        """
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

    def _handle_noclip(self, axis: str, delta: float) -> bool:
        """Allow movement through walls when 'no_clip' cheat is active.

        Checks maze bounds to avoid moving infinitely outside the level.
        """
        if (self.cheats_menu.get_cheat("no_clip").state):
            if axis == 'x':
                wall_limit = self.maze_3d.x * self.maze_3d.scale
                if 0 < self.position.x + delta < wall_limit:
                    return True
            elif axis == 'z':
                wall_limit = -self.maze_3d.y * self.maze_3d.scale
                if wall_limit < self.position.z + delta < 0:
                    return True
        return False

    def _move_axis(self, axis: str, delta: float) -> None:
        """Move along an axis if not blocked."""
        if self._axis_blocked(axis, delta):
            return

        if self.maze_3d and self._walls_limits(axis, delta):
            return

        setattr(self, axis, getattr(self, axis) + delta)

    def _walls_limits(self, axis: str, delta: float) -> bool:
        """Prevent the player from moving outside maze bounds.

        Returns True when the attempted move would go beyond allowed limits.
        """
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

    def _mouse_look(self) -> None:
        """Rotate the player and camera pivot based on mouse movement."""
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
        """Return a movement vector based on keyboard input (WASD)."""
        return Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s'],
        )

    def _move_player(self, move_input: Vec3) -> bool:
        """Apply movement input; return True if moved."""
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
        """Per-frame update handling look, movement and related updates."""
        self._mouse_look()
        is_moving = self._move_player(self._movement_input())

        self._minimap_rotate_player()
        self._handle_pacgums_collisions()
        self._handle_lives_cheat()
        self._apply_breathing(is_moving)

    def _handle_wallhack(self, model: Any) -> None:
        """Toggle model rendering state for the 'wallhack' cheat.

        When active, models are forced to render on top and colored red.
        """
        is_actif = self.cheats_menu.get_cheat("wallhack").state
        model.always_on_top = is_actif
        if is_actif:
            model.color = color.red
        else:
            model.color = color.white

    def _is_inside_square(self, target_pos: Vec3, half_size: float) -> Any:
        """Return True if the player is within an axis-aligned square.

        Used for simple proximity checks against pac-gum positions.
        """
        return (
            self.position.x <= target_pos.x + half_size and
            self.position.x >= target_pos.x - half_size and
            self.position.z <= target_pos.z + half_size and
            self.position.z >= target_pos.z - half_size
        )

    def _handle_pacgums_collisions(self) -> None:
        """Detect and handle collisions with pac-gum entities.

        Hides collected pac-gums and applies wallhack visualization when
        that cheat is active.
        """
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
        """Sync the minimap player's position with the world position."""
        self.mini_map.player.x = self.position.x
        self.mini_map.player.z = self.position.z

    def _minimap_rotate_player(self) -> None:
        """Rotate the minimap player indicator based on mouse movement."""
        self.mini_map.player.rotation_y += mouse.velocity[0] * 40

    def _apply_breathing(self, is_moving: bool) -> None:
        """Apply a subtle vertical camera offset to simulate breathing."""
        if is_moving:
            frequency = 16.0
            amplitude = 0.028
        else:
            frequency = 3.8
            amplitude = 0.008

        amplitude *= self.breathing_strength

        self._breath_t += time.dt * frequency
        target_offset = math.sin(self._breath_t) * amplitude
        self._current_breath_offset += (
            target_offset - self._current_breath_offset
        ) * min(1.0, time.dt * 12.0)
        self.camera_pivot.y = self._base_camera_y + self._current_breath_offset

    def reset_to_spawn(self) -> None:
        """Reset player transform and camera state to initial spawn values."""
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
