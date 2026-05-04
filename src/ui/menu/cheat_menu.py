from typing import Callable
from ursina import Entity, Text, camera, color, mouse
from ..components import MenuButton, slider_cheat, button_cheat, checkbox_cheat

font_path = "assets/fonts/PressStart2P-vaV7.ttf"


class Cheat:
    """Describe one cheat entry and its current state."""

    def __init__(self, name: str, is_cursor: bool = False,
                 is_button: bool = False):
        self.name = name
        self.state: bool | int | float = False
        self.is_cursor = is_cursor
        self.is_button = is_button

    def display(self, parent: Entity, i: int) -> None:
        """Display the control that matches the cheat type.

        Args:
            parent: Menu parent entity.
            i: Cheat index in the menu.
        """
        if self.is_cursor:
            slider_cheat(parent, self.name, i, self.change_state)
        elif self.is_button:
            button_cheat(parent, self.name, i, self.change_state, text='+')
        else:
            checkbox_cheat(parent, self.name, i, self.change_state)

    def change_state(self, state: bool | int | float) -> None:
        """Update the cheat state from the menu widget."""

        self.state = state


class Cheat_menu:
    """Menu container used to display and manage available cheats."""

    def __init__(self, on_exit: Callable[[], None] | None = None):
        self.__cheats: list[Cheat] = []
        self._on_exit = on_exit
        self.menu = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.6, 0.8),
            color=color.rgba32(13, 20, 36, 220),
            position=(0, 0)
        )

        self._frame = Entity(
            parent=self.menu,
            model='quad',
            scale=(1.04, 1.03),
            z=0.01,
            color=color.rgba32(5, 8, 15, 210),
        )

        self._top_line = Entity(
            parent=self.menu,
            model='quad',
            y=0.37,
            z=-0.05,
            scale=(0.9, 0.012),
            color=color.rgba32(82, 210, 255, 180),
        )

        Text(
            text="Cheats",
            parent=self.menu,
            origin=(0, -7),
            color=color.rgb(0.729, 0.980, 1.000),
            scale=2.4,
            z=-0.1,
            font=font_path,
        )

        self.exit_button = MenuButton(
            text='EXIT',
            on_click=self._handle_exit_click,
            y=-0.34,
            width=0.6,
            height=0.1,
        )
        self.exit_button.parent = self.menu
        self.exit_button.z = -0.1

    def show(self) -> None:
        """Show the menu."""
        self.menu.enabled = True
        mouse.locked = False

    def hide(self) -> None:
        """Hide the menu."""
        self.menu.enabled = False
        mouse.locked = True

    def _handle_exit_click(self) -> None:
        """Close the menu or delegate to the provided exit callback."""
        if self._on_exit is not None:
            self._on_exit()
        else:
            self.hide()

    def add_cheat(self, cheat: Cheat, i: int) -> None:
        """Add a cheat entry to the menu and render it.

        Args:
            cheat: Cheat entry to add.
            i: Cheat index in the menu.
        """
        self.__cheats.append(cheat)
        cheat.display(self.menu, i)

    def get_cheat(self, name: str) -> Cheat | None:
        """Return the cheat entry matching the given name.

        Args:
            name: Cheat name to look up.

        Returns:
            The matching cheat, or ``None`` if it does not exist.
        """
        for cheat in self.__cheats:
            if cheat.name == name:
                return cheat
        return None
