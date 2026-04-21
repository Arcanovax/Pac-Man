import math

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
)


class PlayerController(Entity):
    def __init__(
        self,
        speed=10,
        collider_size=Vec3(0.34, 2, 0.34),
        eye_height=1.6,
        fov=100,
        mouse_sensitivity=Vec2(40, 40),
        skin_width=0.04,
        mini_map=None,
<<<<<<< HEAD
        pacgums=None
        mini_map=None,
        pacgums=None
=======
        pacgums=None,
        cheats={},
        maze_3d=None
        
>>>>>>> dc40e28 (cheat)
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
<<<<<<< HEAD
        self.mini_map = mini_map
        self.pacgums = pacgums
=======
        self.cheats = cheats
        self.maze_3d = maze_3d
>>>>>>> dc40e28 (cheat)
        self._breath_t = 0.0
        self._base_camera_y = self.eye_height
        self._current_breath_offset = 0.0
        self.position = mini_map.player_spawn

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

    def _axis_blocked(self, axis, delta):
        if abs(delta) < 0.0001:
            return False
        
        direction = Vec3(1, 0, 0) if axis == 'x' else Vec3(0, 0, 1)
        if delta < 0:
            direction = -direction

        half_width = self.collider_size.x / 2 if axis == 'x' else self.collider_size.z / 2
        distance = half_width + abs(delta) + self.skin_width

        origins = (
            self.world_position + Vec3(0, 0.2, 0),
            self.world_position + Vec3(0, self.collider_size.y * 0.5, 0),
            self.world_position + Vec3(0, self.collider_size.y - 0.2, 0),
        )

        for origin in origins:
            hit = raycast(
                origin,
                direction,
                distance=distance,
                ignore=(self,),
                traverse_target=scene,
            )
            if hit.hit:
                if self._handle_noclip(axis):
                    return False
                return True

        return False
    
    def _handle_noclip(self, axis):
        if (self.cheats.get("no_clip")):
            if axis == 'x':
                wall_limit = self.maze_3d.x * self.maze_3d.scale
                if 0 <= self.position.x <= wall_limit:
                    return True
            elif axis == 'z':
                wall_limit = -self.maze_3d.y * self.maze_3d.scale
                if wall_limit <= self.position.z <= 0:
                    return True

    def _move_axis(self, axis, delta):
        if self._axis_blocked(axis, delta):
            return
        setattr(self, axis, getattr(self, axis) + delta)

    def update(self):
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[1]
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -89, 89)

        move_input = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s'],
        )
        is_moving = move_input != Vec3(0, 0, 0)

        if is_moving:
            move_input = move_input.normalized() * self.speed * time.dt
            world_move = (self.right * move_input.x) + (self.forward * move_input.z)

            self._move_axis('x', world_move.x)
            self._move_axis('z', world_move.z)
            self._minimap_move_player()

        self._minimap_rotate_player()
        self._handle_pacgums_collisions()
        self._apply_breathing(is_moving)

    def _handle_pacgums_collisions(self):
        for gum in self.pacgums.get('normal'):
            gum_pos = gum.model.position
            if (self.position.x <= gum_pos.x + 1 and
               self.position.x >= gum_pos.x - 1 and
               self.position.z <= gum_pos.z + 1 and
               self.position.z >= gum_pos.z - 1):
                gum.hide()

        for gum in self.pacgums.get('super'):
            gum_pos = gum.model.position
            if (self.position.x <= gum_pos.x + 2 and
               self.position.x >= gum_pos.x - 2 and
               self.position.z <= gum_pos.z + 2 and
               self.position.z >= gum_pos.z - 2):
                gum.hide()

    def _minimap_move_player(self):
        self.mini_map.player.x = self.position.x
        self.mini_map.player.z = self.position.z

    def _minimap_rotate_player(self):
        self.mini_map.player.rotation_y += mouse.velocity[0] * 40

    def _apply_breathing(self, is_moving):
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
