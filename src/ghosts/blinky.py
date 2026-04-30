from ursina import load_texture
from .ghost_base import Ghost


class Blinky(Ghost):
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player,
    ):
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
