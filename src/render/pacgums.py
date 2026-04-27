from ursina import Entity, Vec3, color, Mesh
from random import shuffle
from enum import Enum


class Pacgum_Type(Enum):
    normal = "normal"
    super = "super"


class Pacgums_Manager():
    def __init__(self, scale_maze, config, pacgums_zone, minimap, size):
        self.width = size[0]
        self.height = size[1]
        self.scale = scale_maze
        self.pacgums_zone = pacgums_zone
        self.minimap = minimap
        self.nb_pacgum = config.pacgum
        self.pacgums = {
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

    def gen_super_pacgum(self, pos):
        type = Pacgum_Type.super
        self.pacgums.get(type.value).append(Pacgum(self, pos, type))
        if (pos[0], pos[2]) in self.pacgums_zone:
            self.pacgums_zone.remove((pos[0], pos[2]))

    def gen_pacgum(self, pos):
        type = Pacgum_Type.normal
        self.pacgums.get(type.value).append(Pacgum(self, pos, type))


class Pacgum:
    def __init__(self, manager: Pacgums_Manager,
                 position: Vec3, type_gum: Pacgum_Type):
        self.position = position
        self.type_gum = type_gum
        self.manager = manager
        self.model_scale = 1
        self.visible = True
        if self.type_gum == Pacgum_Type.super:
            self.model_scale = 2
        self.gen_on_game()
        self.gen_on_minimap()


    def gen_on_game(self):
        self.model = Entity(
            model="sphere",
            scale=self.model_scale,
            add_to_scene_entities=False,
            collider=None,
            position=self.position * self.manager.scale
        )

    def gen_on_minimap(self):
        self.sprite = Entity(
            parent=self.manager.minimap.get_ui_map(),
            model='sphere',
            color=color.white,
            scale=(self.model_scale, 0, self.model_scale),
            position=self.position * self.manager.scale
        )

    def hide(self):
        self.visible = False
        self.model.enabled = False
        self.sprite.enabled = False
