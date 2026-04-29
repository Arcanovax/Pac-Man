import random
from collections import deque
from typing import Any
from ursina.color import rgba32

import math

from ursina import Entity, Vec3, color, time

GridPos = tuple[int, int]

STATE_CHASE = "chase"
STATE_FRIGHTENED = "frightened"
STATE_EATEN = "eaten"

FRIGHTENED_SPEED_FACTOR = 0.72
PATH_REFRESH_INTERVAL = 0.20


class Ghost(Entity):
    def __init__(
        self,
        name: str,
        spawn_coords: GridPos,
        tile_size: float,
        walkable_cells: set[GridPos],
        maze_grid: list[list[int]],
        scatter_target: GridPos,
        player: Entity,
        model: str,
        speed: float = 4.4,
    ):
        spawn_world = Vec3(
            spawn_coords[0] * tile_size,
            1.2,
            spawn_coords[1] * tile_size,
        )

        super().__init__(
            name=name,
            model=model,
            scale=(10.0, 10.0, 10.0),
            position=spawn_world,
            collider="box",
        )

        self.spawn_coords = spawn_coords
        self.tile_size = tile_size
        self.walkable_cells = walkable_cells
        self.maze_grid = maze_grid
        self.scatter_target = scatter_target
        self.player = player
        self.base_speed = speed
        self.speed = speed

        self.state = STATE_CHASE
        self.path: list[GridPos] = []
        self._path_refresh_cd = 0.0
        self._frightened_timer = 0.0
        self._respawn_timer = 0.0
        self._current_target: GridPos | None = None
        self.last_position = Vec3(
            self.position.x,
            self.position.y,
            self.position.z,
        )
        self.rotation = (0, 0, 0)

        self.collider.trigger = True
        self.is_trigger = True

    def _grid_to_world(self, x: int, y: int) -> Vec3:
        return Vec3(
            x * self.tile_size,
            1.2,
            y * self.tile_size
        )

    def _world_to_grid(self, world_pos: Vec3) -> GridPos:
        return (
            int(round(world_pos.x / self.tile_size)),
            int(round(world_pos.z / self.tile_size)),
        )

    def _closest_walkable(self, target: GridPos) -> GridPos:
        if target in self.walkable_cells:
            return target
        return min(
            self.walkable_cells,
            key=lambda cell: (
                abs(cell[0] - target[0]) +
                abs(cell[1] - target[1])
            ),
        )

    def _near_cell(self, cell: GridPos) -> list[GridPos]:
        x_pos, y_pos = cell
        row = -y_pos
        if (
            row < 0
            or row >= len(self.maze_grid)
            or x_pos < 0
            or x_pos >= len(self.maze_grid[row])
        ):
            return []

        wall_bits = f"{int(self.maze_grid[row][x_pos]):04b}"
        has_north = wall_bits[3] == "1"
        has_east = wall_bits[2] == "1"
        has_south = wall_bits[1] == "1"
        has_west = wall_bits[0] == "1"

        near_cell: list[GridPos] = []
        if not has_east and (x_pos + 1, y_pos) in self.walkable_cells:
            near_cell.append((x_pos + 1, y_pos))
        if not has_west and (x_pos - 1, y_pos) in self.walkable_cells:
            near_cell.append((x_pos - 1, y_pos))
        if not has_north and (x_pos, y_pos + 1) in self.walkable_cells:
            near_cell.append((x_pos, y_pos + 1))
        if not has_south and (x_pos, y_pos - 1) in self.walkable_cells:
            near_cell.append((x_pos, y_pos - 1))

        return near_cell

    def _build_path(
        self,
        start: GridPos,
        goal: GridPos,
    ) -> list[GridPos]:
        if start == goal:
            return [start]

        queue = deque([start])
        came_from: dict[GridPos, GridPos | None] = {start: None}

        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for near_cell in self._near_cell(current):
                if near_cell in came_from:
                    continue
                came_from[near_cell] = current
                queue.append(near_cell)

        if goal not in came_from:
            return [start]

        path = [goal]
        current_step = goal
        while True:
            parent = came_from[current_step]
            if parent is None:
                break
            current_step = parent
            path.append(current_step)
        path.reverse()
        return path

    def _player_grid(self) -> GridPos:
        player_cell = self._world_to_grid(self.player.position)
        return self._closest_walkable(player_cell)

    def get_chase_target(self, blinky: Any = None) -> GridPos:
        return self._player_grid()

    def set_frightened(self, duration: float) -> None:
        if self.state == STATE_EATEN:
            return
        self.state = STATE_FRIGHTENED
        self._frightened_timer = max(self._frightened_timer, float(duration))
        self.speed = self.base_speed * FRIGHTENED_SPEED_FACTOR
        self.color = color.azure

    def reset_to_spawn(self) -> None:
        self.state = STATE_CHASE
        self.speed = self.base_speed
        self._frightened_timer = 0.0
        self._respawn_timer = 0.0
        self.path.clear()
        self._current_target = None
        self.color = rgba32(r=255, g=255, b=255, a=255)
        self.enabled = True
        self.visible = True
        self.position = self._grid_to_world(*self.spawn_coords)
        self.last_position = Vec3(
            self.position.x,
            self.position.y,
            self.position.z,
        )
        self.rotation = (0, 0, 0)

    def on_eaten(self, respawn_delay: float = 3.0) -> None:
        self.state = STATE_EATEN
        self._respawn_timer = max(0.1, float(respawn_delay))
        self.enabled = True
        self.visible = False
        self.path.clear()
        self._current_target = None
        self.rotation = (0, 0, 0)

    def _select_target(self, blinky: Any) -> GridPos:
        if self.state == STATE_FRIGHTENED:
            if random.random() < 0.33:
                return random.choice(tuple(self.walkable_cells))
            return self.scatter_target
        return self.get_chase_target(blinky)

    def _face_direction(self, direction: Vec3) -> None:
        if direction.length() < 0.001:
            return

        direction = Vec3(direction.x, 0, direction.z).normalized()
        target_yaw = math.degrees(math.atan2(direction.x, direction.z))
        self.animate_rotation((0.0, target_yaw, 0.0), duration=0.10)

    def _move_on_path(self) -> None:
        if len(self.path) < 2:
            return

        next_cell = self.path[1]
        target_world = self._grid_to_world(*next_cell)
        direction = target_world - self.position
        direction.y = 0
        self._face_direction(direction)
        distance = direction.length()
        if distance < 0.001:
            self.position = target_world
            self.path.pop(0)
            return

        max_step = self.speed * time.dt * self.tile_size * 0.35
        if distance <= max_step:
            self.position = target_world
            self.path.pop(0)
            return

        direction = direction.normalized()
        self.position += direction * max_step

    def update_ai(self, blinky: Any = None) -> None:
        self.last_position = Vec3(
            self.position.x,
            self.position.y,
            self.position.z,
        )

        if self.state == STATE_EATEN:
            self._respawn_timer -= time.dt
            if self._respawn_timer <= 0:
                self.reset_to_spawn()
            return

        if self._frightened_timer > 0:
            self._frightened_timer -= time.dt
            if self._frightened_timer <= 0:
                self.state = STATE_CHASE
                self.speed = self.base_speed
                self.color = self.base_color

        current = self._closest_walkable(self._world_to_grid(self.position))
        target_raw = self._select_target(blinky)
        target = self._closest_walkable(target_raw)

        self._path_refresh_cd -= time.dt
        should_refresh = (
            self._path_refresh_cd <= 0
            or not self.path
            or self._current_target != target
        )
        if should_refresh:
            self.path = self._build_path(current, target)
            self._current_target = target
            self._path_refresh_cd = PATH_REFRESH_INTERVAL

        self._move_on_path()


class Blinky(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Entity,
    ):
        super().__init__(
            name="Blinky",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model="assets/models/ghost_red.glb",
            speed=4.7,
        )


class Pinky(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Entity,
    ):
        super().__init__(
            name="Pinky",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model="assets/models/ghost_pink.glb",
            speed=4.45,
        )

    def get_chase_target(self, blinky: Any = None) -> tuple[int, int]:
        ahead = self.player.position + (
            self.player.forward * self.tile_size * 3
        )
        return self._closest_walkable(self._world_to_grid(ahead))


class Inky(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Entity,
    ):
        super().__init__(
            name="Inky",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model="assets/models/ghost_cyan.glb",
            speed=4.35,
        )

    def get_chase_target(self, blinky: Any = None) -> tuple[int, int]:
        ahead = self.player.position + (
            self.player.forward * self.tile_size * 2
        )
        if blinky is None:
            return self._closest_walkable(self._world_to_grid(ahead))

        vec = ahead - blinky.position
        inky_target = ahead + vec
        return self._closest_walkable(self._world_to_grid(inky_target))


class Clyde(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Entity,
    ):
        super().__init__(
            name="Clyde",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model="assets/models/ghost_orange.glb",
            speed=4.10,
        )

    def get_chase_target(self, blinky: Any = None) -> tuple[int, int]:
        player_cell = self._player_grid()
        own_cell = self._closest_walkable(self._world_to_grid(self.position))
        dist = (
            abs(player_cell[0] - own_cell[0]) +
            abs(player_cell[1] - own_cell[1])
        )
        if dist <= 5:
            return self.scatter_target
        return player_cell
