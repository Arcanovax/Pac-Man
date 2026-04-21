from ursina import Entity, camera, color, duplicate


class MiniMap(Entity):
    def __init__(self, maze_3d, size, map_scale):
        super().__init__(parent=camera.ui)
        self.map_scale = map_scale
        self.player_spawn = maze_3d.player_spawn
        self.display_minimap(maze_3d.walls, map_scale)

    def display_minimap(self, walls, scale):
        self.minimap_walls = duplicate(walls)
        self.minimap_walls.parent = self
        self._panel_center_x = 0.7
        self._panel_center_y = 0.3

        min_bound, max_bound = self.minimap_walls.getTightBounds()
        model_size = max_bound - min_bound
        center_x = (max_bound.x + min_bound.x) / 2
        center_z = (max_bound.z + min_bound.z) / 2

        max_dim = max(model_size.x, model_size.z)
        scale_factor = scale / max_dim

        self.minimap_walls.scale = (scale_factor, 0.1, scale_factor)

        self.minimap_walls.texture = None
        self.minimap_walls.color = color.rgb(0.729, 0.980, 1.000)
        self.minimap_walls.collider = None
        self.minimap_walls.rotation_x = -90

        self.minimap_walls.position = (
            self._panel_center_x - (center_x * scale_factor),
            self._panel_center_y - (center_z * scale_factor),
            -0.10,
        )

        bg_width = model_size.x * scale_factor
        bg_height = model_size.z * scale_factor
        frame_h = bg_height + 0.08
        inner_w = bg_width + 0.04
        inner_h = bg_height + 0.04

        Entity(
            parent=self,
            model='quad',
            color=color.rgba(0.020, 0.031, 0.063, 0.74),
            scale=(inner_w, inner_h),
            position=(self._panel_center_x, self._panel_center_y),
            z=0.03,
        )

        Entity(
            parent=self,
            model='quad',
            color=color.rgba(0.322, 0.824, 1.000, 0.36),
            scale=(inner_w, 0.005),
            position=(
                self._panel_center_x,
                self._panel_center_y + (inner_h * 0.5) - 0.01,
            ),
            z=0.02,
        )

        self.bg = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0.071, 0.098, 0.169, 0.84),
            scale=(bg_width, bg_height),
            position=(self._panel_center_x, self._panel_center_y),
            z=0.01,
        )

        self._title = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0.110, 0.161, 0.251, 0.82),
            scale=(bg_width * 0.56, 0.03),
            position=(
                self._panel_center_x,
                self._panel_center_y + (frame_h / 2) + 0.022,
            ),
            z=0.03,
        )
        self.player = Entity(
            parent=self.minimap_walls,
            model='pacman.obj',
            color=color.yellow,
            scale=(0.125, 0, 0.125),
            position=self.player_spawn,
            rotation_y=90
        )

    def get_ui_map(self):
        return self.minimap_walls
