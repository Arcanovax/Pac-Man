from ursina import load_texture
from .ghost_base import Ghost
from typing import Any


class Blinky(Ghost):
    """Red ghost that directly chases the player."""
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Any,
    ):
        """
        Initialize Blinky ghost.
        
        Args:
            spawn_coords: Grid coordinates where Blinky spawns.
            tile_size: Size of each grid tile in world units.
            walkable_cells: Set of grid cells Blinky can traverse.
            maze_grid: 2D grid representing maze walls in binary format.
            scatter_target: Grid coordinates for scatter mode target.
            player: Reference to the player entity.
        """
        self.model_base = "assets/models/ghost_red.glb"
        self.blips_base = load_texture("assets/textures/red_ghost.png")
        super().__init__(
            name="Blinky",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model=self.model_base,
            speed=4.7,
        )
        self.blips = self.blips_base
