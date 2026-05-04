from ursina import Slider, Text, color, Entity
from typing import Callable, Any

font_path = "assets/fonts/PressStart2P-vaV7.ttf"


class slider_cheat(Slider):
    """Custom slider button for cheat visual.
    Args:
        Slider: Slider from ursina
    """
    def __init__(
        self,
        parent: Entity,
        name: str,
        i: int,
        _change_state: Callable[[Any], None],
    ) -> None:
        """Init the slider button for the cheat.

        Args:
            parent (Entity): Cheat menu
            name (str): name of the cheat
            i (int): index of the cheat
            _change_state (Callable[[Any], None]): function to change the
                state.
        """
        self._change_state = _change_state
        self.last_value = None
        self.pos_x = 0.4
        self.pos_y = -0.08 - i * -0.075

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
            color=color.rgb(0.322, 0.824, 1.000),
            origin=(-0.5, 0),
            x=-self.pos_x,
            y=self.pos_y,
            z=-0.1,
            font=font_path
        )
        self.bg.color = color.rgb(0.322, 0.824, 1.000)
        self.knob.color = color.white
        self.knob.scale = 2

    def update(self) -> None:
        """Update the value of the state of the cheat
        """
        super().update()
        if self.value == self.last_value:
            return
        self._change_state(self.value)
        self.last_value = self.value
