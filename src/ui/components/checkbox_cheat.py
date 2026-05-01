from typing import Callable, Any
from ursina import Button, Text, Entity, color

font_path = "assets/fonts/PressStart2P-vaV7.ttf"

class checkbox_cheat(Button):  # type: ignore
    def __init__(self, parent: Entity, name: str, i: int, _change_state: Callable[[Any], None]) -> None:
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
            color=color.rgb(0.322, 0.824, 1.000),
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
        self.indicator.color = (
            color.rgb(0.322, 0.824, 1.000)
            if self.activated
            else color.black
        )
