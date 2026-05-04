from typing import Callable, Any
from ursina import Button, Text, color, Entity

font_path = "assets/fonts/PressStart2P-vaV7.ttf"


class button_cheat(Button):  # type: ignore
    """Custom button for cheat visual.
    Args:
        Button: Button from ursina
    """
    def __init__(
        self,
        parent: Entity,
        name: str,
        i: int,
        _change_state: Callable[[Any], None],
        text: str | None = None,
    ) -> None:
        """Init the button for the cheat.

        Args:
            parent (Entity): Cheat menu
            name (str): name of the cheat
            i (int): index of the cheat
            _change_state (Callable[[Any], None]): function to change the state
            text (str | None, optional): text inside the button. Defaults to
                None.
        """
        self._change_state = _change_state
        self.state = 0
        self.pos_x = 0.4
        self.pos_y = -0.08 - i * -0.075
        self.text_button = text
        super().__init__(
            parent=parent,
            scale=(0.03, 0.03),
            x=self.pos_x,
            y=self.pos_y,
            color=color.rgb(0.322, 0.824, 1.000),
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
        self.text_button = Text(
            parent=self,
            text=self.text_button,
            color=color.black,
            z=-0.2,
            scale=60,
            origin=(0.05, 0.05),
        )

    def on_click(self) -> None:
        """Update the value of the state of the cheat
        """
        self.state += 1
        self._change_state(self.state)
