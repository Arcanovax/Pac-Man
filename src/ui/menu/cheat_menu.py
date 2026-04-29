from ursina import Entity, Text, camera, color, mouse, Button, Slider, Ursina

font_path = "assets/fonts/PressStart2P-vaV7.ttf"


class Cheat():
    def __init__(self, name, is_cursor=False, is_button=False):
        self.name = name
        self.state = False
        self.is_cursor = is_cursor
        self.is_button = is_button

    def display(self, parent, i) -> None:
        if self.is_cursor:
            slider_cheat(parent, self.name, i, self.change_state)
        elif self.is_button:
            button_cheat(parent, self.name, i, self.change_state, text='+')
        else:
            checkbox_cheat(parent, self.name, i, self.change_state)

    def change_state(self, state) -> None:
        self.state = state


class Cheat_menu():
    def __init__(self):
        self.__cheats = []
        self.menu = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.5, 0.8),
            color=color.black,
            position=(0, 0)
        )
        Text(
            text="Cheats",
            parent=self.menu,
            origin=(0, -7),
            color=color.red,
            scale=2.4,
            z=-0.1,
            font=font_path,
        )

    def show(self) -> None:
        self.menu.enabled = True
        mouse.locked = False

    def hide(self) -> None:
        self.menu.enabled = False
        mouse.locked = True

    def add_cheat(self, cheat: Cheat, i) -> None:
        self.__cheats.append(cheat)
        cheat.display(self.menu, i)

    def get_cheat(self, name: str) -> None:
        for cheat in self.__cheats:
            if cheat.name == name:
                return cheat
        return None


class slider_cheat(Slider):
    def __init__(self, parent, name, i, _change_state):
        self._change_state = _change_state
        self.last_value = None
        self.pos_x = 0.4
        self.pos_y = 0 - i*-0.075

        super().__init__(
            parent=parent,
            x=0.1,
            y=self.pos_y,
            min=5,
            max=30,
            z=-0.1,
            default=10,
            bar_color=color.white,
            step=5,
            scale=0.6,
            )

        self.text_name = Text(
            text=name,
            parent=parent,
            scale=1,
            color=color.red,
            origin=(-0.5, 0),
            x=-self.pos_x,
            y=self.pos_y,
            z=-0.1,
            font=font_path
        )
        self.bg.color = color.red
        self.knob.color = color.white
        self.knob.scale = 2

    def update(self) -> None:
        super().update()
        if self.value == self.last_value:
            return
        self._change_state(self.value)
        self.last_value = self.value


class button_cheat(Button):
    def __init__(self, parent, name, i, _change_state, text=None):
        self._change_state = _change_state
        self.state = False
        self.pos_x = 0.4
        self.pos_y = 0 - i*-0.075
        self.text_button = text
        super().__init__(
            parent=parent,
            scale=(0.03, 0.03),
            x=self.pos_x,
            y=self.pos_y,
            color=color.red,
            model='quad',
            z=-0.1,
        )
        self.text_name = Text(
            text=name,
            parent=parent,
            scale=1,
            color=color.red,
            origin=(-0.5, 0),
            x=-self.pos_x,
            y=self.pos_y,
            z=-0.1,
            font=font_path
        )
        self.text_button = Text(
            parent=self,
            text=self.text_button,
            color=color.black,
            z=-0.2,
            scale=60,
            origin=(0.05, 0.05),
        )

    def on_click(self) -> None:
        self._change_state(True)


class checkbox_cheat(Button):
    def __init__(self, parent, name, i, _change_state):
        self._change_state = _change_state
        self.pos_x = 0.4
        self.pos_y = 0 - i*-0.075
        super().__init__(
            parent=parent,
            scale=(0.03, 0.03),
            x=self.pos_x,
            y=self.pos_y,
            color=color.white,
            model='quad',
            z=-0.1,
        )
        self.text_name = Text(
            text=name,
            parent=parent,
            scale=1,
            color=color.red,
            origin=(-0.5, 0),
            x=-self.pos_x,
            y=self.pos_y,
            z=-0.1,
            font=font_path
        )
        self.activated = False
        self.indicator = Entity(
            parent=parent,
            model='quad',
            scale=0.025,
            color=color.black,
            x=self.pos_x,
            y=self.pos_y,
            z=-0.2
        )

    def on_click(self) -> None:
        self.activated = not self.activated
        self._change_state(self.activated)
        self.indicator.color = color.red if self.activated else color.black


if __name__ == "__main__":
    app = Ursina()
    app.run()
