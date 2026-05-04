from typing import Callable
from ursina import (
    Entity,
    Ursina,
    camera,
    color as colors,
    destroy,
    mouse,
)

from ...logger import Logger
from ..components import MenuButton


class PauseMenuManager:
    """Controls the in-game pause menu lifecycle and UI.

    Responsible for showing and hiding the pause UI, wiring resume and
    quit callbacks, and building a retro-styled frame for the menu.
    """
    def __init__(self, app: Ursina) -> None:
        self.app = app
        self.is_paused = False
        self.pause_entities: list[Entity] = []
        self.pause_buttons: list[MenuButton] = []
        self.on_resume: Callable[[], None] | None = None
        self.on_quit_to_menu: Callable[[], None] | None = None
        self.font_path = "assets/fonts/PressStart2P-vaV7.ttf"

    def show(
        self,
        on_resume: Callable[[], None],
        on_quit_to_menu: Callable[[], None],
    ) -> None:
        """Open the pause menu and register resume/quit callbacks."""
        if self.is_paused:
            return

        self.is_paused = True
        self.on_resume = on_resume
        self.on_quit_to_menu = on_quit_to_menu
        mouse.locked = False

        Logger.debug("Pause menu opened")
        self._build_pause_ui()

    def hide(self) -> None:
        """Hide the pause menu and resume gameplay."""
        if not self.is_paused:
            return

        self.is_paused = False
        mouse.locked = True

        self._clear_pause_ui()
        Logger.debug("Pause menu closed - gameplay resumed")

    def _clear_pause_ui(self) -> None:
        """Destroy pause UI entities and clear internal lists."""
        for entity in self.pause_entities:
            destroy(entity)
        self.pause_entities.clear()

        for button in self.pause_buttons:
            destroy(button)
        self.pause_buttons.clear()

    def _build_pause_ui(self) -> None:
        """Construct the pause menu UI and wire button callbacks."""
        self.pause_entities.extend(self._build_retro_frame())

        title = Entity(
            parent=camera.ui,
            model="quad",
            y=0.2,
            z=0.04,
            scale=(0.4, 0.08),
            color=colors.rgba(0.0, 0.0, 0.0, 0.0),
        )
        self.pause_entities.append(title)

        from ursina import Text
        pause_title = Text(
            parent=camera.ui,
            text="PAUSED",
            y=0.2,
            z=-0.10,
            origin=(0, 0),
            font=self.font_path,
            scale=2.0,
            color=colors.rgb(0.729, 0.980, 1.000),
        )
        self.pause_entities.append(pause_title)

        def _on_resume() -> None:
            if self.on_resume:
                self.on_resume()

        def _on_quit() -> None:
            self._clear_pause_ui()
            if self.on_quit_to_menu:
                self.on_quit_to_menu()

        resume_button = MenuButton(
            text="RESUME",
            on_click=_on_resume,
            y=0.05,
        )
        self.pause_buttons.append(resume_button)
        self.pause_entities.append(resume_button)

        quit_button = MenuButton(
            text="QUIT TO MENU",
            on_click=_on_quit,
            y=-0.10,
        )
        self.pause_buttons.append(quit_button)
        self.pause_entities.append(quit_button)

    def _build_retro_frame(self) -> list[Entity]:
        frame_entities: list[Entity] = []

        frame_entities.append(Entity(
            parent=camera.ui,
            model="quad",
            y=0.05,
            z=0.04,
            scale=(0.50, 0.55),
            color=colors.rgba(0.051, 0.078, 0.141, 0.745),
        ))

        frame_entities.append(Entity(
            parent=camera.ui,
            model="quad",
            y=0.05,
            z=0.03,
            scale=(0.48, 0.53),
            color=colors.rgba(0.020, 0.031, 0.063, 0.608),
        ))

        frame_entities.append(Entity(
            parent=camera.ui,
            model="quad",
            y=0.32,
            z=0.02,
            scale=(0.44, 0.008),
            color=colors.rgba(0.322, 0.824, 1.000, 0.569),
        ))

        frame_entities.append(Entity(
            parent=camera.ui,
            model="quad",
            y=-0.22,
            z=0.02,
            scale=(0.44, 0.008),
            color=colors.rgba(0.322, 0.824, 1.000, 0.569),
        ))

        return frame_entities
