from ursina import Entity, Vec3, color, scene


class Maze_3d():
    def __init__(self, maze, scale):
        self.maze = maze
        self.scale = scale
        self.walls_entity = []
        self.floors = []
        self.pacgums_zone = []
        self.walls = Entity(parent=scene)
        for y in range(len(maze)):
            for x in range(len(maze[y])):
                self.create_walls(x, y)
        self.y = y
        self.x = x
        self.walls.combine()
        self.walls.texture = "assets/textures/wall.jpg"
        self.player_spawn = Vec3((x/2)*scale, 0, (-y/2)*scale)
        self.gen_floor(x, y, 0, scale)
        self.gen_floor(x, y, 4, scale)

    def get_walls(self, val: int) -> dict[str, bool | int]:
        bits = f"{int(val):04b}"
        return {
            "NORTH": bits[3] == '1',
            "EAST": bits[2] == '1',
            "SOUTH": bits[1] == '1',
            "WEST": bits[0] == '1',
            "NB": val
        }

    def gen_floor(self, x, y, hight, scale):
        Entity_position = ((x/2)*scale, hight, (-y/2)*scale)
        Entity_scale = ((x+1)*scale, 1, (-y-1)*scale)
        floor_texture_path = "assets/textures/floor.jpg"
        floor_entity = Entity(
            model='cube',
            position=Entity_position,
            scale=Entity_scale,
            collider='box',
            texture=str(floor_texture_path),
            texture_scale=(5, 5)
            )
        self.floors.append(floor_entity)
        return floor_entity

    def gen_wall(self, position, scale):
        wall_texture_path = "assets/textures/wall.jpg"
        wall_position = (position[0] * self.scale,
                         position[1],
                         position[2] * self.scale)
        wall_scale = Vec3(
            scale[0] * self.scale,
            scale[1] * self.scale,
            scale[2] * self.scale,
        )

        Entity(
            model=None,
            position=wall_position,
            scale=wall_scale,
            collider='box',
            visible=False,
            parent=self.walls,
        )

        return Entity(
            model='cube',
            position=wall_position,
            color=color.gray,
            scale=wall_scale,
            texture=str(wall_texture_path),
            parent=self.walls
        )

    def create_walls(self, x, y):
        y = -y
        walls = self.get_walls(self.maze[-y][x])
        pos = [model.position for model in self.walls_entity]
        if walls.get('NB') == 15:
            return
        else:
            self.pacgums_zone.append((x, y))
            if (walls.get('NORTH') is True and
               not (x*self.scale, 2, (y+0.5)*self.scale) in pos):
                self.walls_entity.append(
                    self.gen_wall((x, 2, (y+0.5)), (1.2, 1, 0.2))
                )
            if (walls.get('SOUTH') is True and
               not (x*self.scale, 2, (y-0.5)*self.scale) in pos):
                self.walls_entity.append(
                    self.gen_wall(
                        (x, 2, (y-0.5)),
                        (1.2, 1, 0.2)
                    )
                )
            if (walls.get('EAST') is True and
               not ((x+0.5)*self.scale, 2, y*self.scale) in pos):
                self.walls_entity.append(
                    self.gen_wall(
                        ((x+0.5), 2, y),
                        (0.2, 1, 1.2)
                    )
                )
            if (walls.get('WEST') is True and
               not ((x-0.5)*self.scale, 2, y*self.scale) in pos):
                self.walls_entity.append(
                    self.gen_wall(
                        ((x-0.5), 2, y),
                        (0.2, 1, 1.2)
                    )
                )
