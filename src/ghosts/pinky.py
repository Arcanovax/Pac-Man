from typing import Any
from ursina import load_texture
from .ghost_base import Ghost


class Pinky(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Any,
    ):
        self.model_base = "assets/models/ghost_pink.glb"
        self.blips_base = load_texture("assets/textures/pink_ghost.png")
        super().__init__(
            name="Pinky",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model=self.model_base,
            speed=4.45,
        )
        self.blips = self.blips_base

    def get_chase_target(self, blinky: Any = None) -> tuple[int, int]:
        ahead = self.player.position + (
            self.player.forward * self.tile_size * 3
        )
        return self._closest_walkable(self._world_to_grid(ahead))
