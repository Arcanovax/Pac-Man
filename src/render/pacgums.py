from ursina import Entity, Vec3, color
from random import shuffle
from enum import Enum
from .minimap import MiniMap
from ..parsing.model import ConfigModel


class Pacgum_Type(Enum):
    """Enumeration for the types of pacgums available."""
    normal = "normal"
    super = "super"


class Pacgums_Manager():
    """Manages the generation and state of all pacgums in the level."""
    def __init__(
        self,
        scale_maze: int,
        config: ConfigModel,
        pacgums_zone: list[tuple[int, int]],
        minimap: MiniMap,
        size: tuple[int, int],
        current_level: int
    ) -> None:
        """Initializes the manager and spawns standard and super pacgums.

        Args:
            scale_maze: The global scale applied to the maze representation.
            config: Reference to the configuration model.
            pacgums_zone: Coordinates of all valid cells for spawning pacgums.
            minimap: UI minimap reference to draw pacgums icons.
            size: Width and Height of the level maze grid.
            current_level: Index of the current level to retrieve config details.
        """
        self.width = size[0]
        self.height = size[1]
        self.scale = scale_maze
        self.pacgums_zone = pacgums_zone
        self.minimap = minimap
        self.nb_pacgum = config.level[current_level].pacgum
        self.pacgums: dict[str, list[Pacgum]] = {
            "normal": [],
            "super": []
        }

        self.gen_super_pacgum(Vec3(0, 0.25, 0))
        self.gen_super_pacgum(Vec3(0, 0.25, -self.height+1))
        self.gen_super_pacgum(Vec3(self.width-1, 0.25, 0))
        self.gen_super_pacgum(Vec3(self.width-1, 0.25, -self.height+1))
        shuffle(self.pacgums_zone)
        for i in range(self.nb_pacgum):
            pos = Vec3(self.pacgums_zone[i][0], 0.15, self.pacgums_zone[i][1])
            self.gen_pacgum(pos)

    def gen_super_pacgum(self, pos: Vec3) -> None:
        """Instantiates a single super pacgum object in the map.

        Args:
            pos: 3D vector representing its localized coordinates across the grid.
        """
        type = Pacgum_Type.super
        self.pacgums[type.value].append(Pacgum(self, pos, type))
        if (pos[0], pos[2]) in self.pacgums_zone:
            self.pacgums_zone.remove((pos[0], pos[2]))

    def gen_pacgum(self, pos: Vec3) -> None:
        """Instantiates a normal pacgum object in the map.

        Args:
            pos: 3D coordinate vector over the map grid.
        """
        type = Pacgum_Type.normal
        self.pacgums[type.value].append(Pacgum(self, pos, type))


class Pacgum:
    """Individual pacgum element that can be consumed by the player."""
    def __init__(self, manager: Pacgums_Manager,
                 position: Vec3, type_gum: Pacgum_Type) -> None:
        """Initializes a new pacgum entity in both the 3D scene and the UI minimap.

        Args:
            manager: Reference to the centralized Pacgums_Manager running.
            position: Spatial origin location within grid coordinates.
            type_gum: Target Enum type defining this object's visual rules.
        """
        self.position = position
        self.type_gum = type_gum
        self.manager = manager
        self.model_scale = 1
        self.visible = True
        if self.type_gum == Pacgum_Type.super:
            self.model_scale = 2
        self.gen_on_game()
        self.gen_on_minimap()

    def gen_on_game(self) -> None:
        """Instantiates the base 3D entity sphere for the 3D scene."""
        self.model = Entity(
            model="sphere",
            scale=self.model_scale,
            add_to_scene_entities=False,
            collider=None,
            position=self.position * self.manager.scale
        )

    def gen_on_minimap(self) -> None:
        """Instantiates the minimap sprite representing this pacgum."""
        self.sprite = Entity(
            parent=self.manager.minimap.get_ui_map(),
            model='sphere',
            color=color.white,
            scale=(self.model_scale, 0, self.model_scale),
            position=self.position * self.manager.scale
        )

    def hide(self) -> None:
        """Hides both the 3D entity and map sprite from rendering.

        Also mutates its visible state to allow tracking scoring.
        """
        self.visible = False
        self.model.enabled = False
        self.sprite.enabled = False
