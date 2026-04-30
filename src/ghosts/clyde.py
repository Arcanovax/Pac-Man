from ursina import load_texture
from typing import Any
from .ghost_base import Ghost


class Clyde(Ghost):
    """Orange ghost with a shy/ambivalent chase behavior.

    Clyde either chases the player or scatters to its corner depending on
    the distance to the player.
    """
    def __init__(
        self,
        spawn_coords: tuple[int, int],
        tile_size: float,
        walkable_cells: set[tuple[int, int]],
        maze_grid: list[list[int]],
        scatter_target: tuple[int, int],
        player: Any,
    ):
        self.model_base = "assets/models/ghost_orange.glb"
        self.blips_base = load_texture("assets/textures/orange_ghost.png")
        super().__init__(
            name="Clyde",
            spawn_coords=spawn_coords,
            tile_size=tile_size,
            walkable_cells=walkable_cells,
            maze_grid=maze_grid,
            scatter_target=scatter_target,
            player=player,
            model=self.model_base,
            speed=4.10,
        )
        self.blips = self.blips_base

    def get_chase_target(self, blinky: Any = None) -> tuple[int, int]:
        """Return Clyde's chase target cell.

        If Clyde is within a short distance of the player it will retreat to
        its scatter target; otherwise it will chase the player's cell.
        """
        player_cell = self._player_grid()
        own_cell = self._closest_walkable(self._world_to_grid(self.position))
        dist = (
            abs(player_cell[0] - own_cell[0]) +
            abs(player_cell[1] - own_cell[1])
        )
        if dist <= 5:
            return self.scatter_target
        return player_cell
