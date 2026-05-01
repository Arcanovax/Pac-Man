from ursina import Entity, Text, camera, color as colors, destroy

from ..components import MenuButton


class OverlayMenuManager:
    """Manager for full-screen overlay menus (highscores, instructions).

    Temporarily hides the main menu buttons and displays a scrollable
    list of rows with a title. Provides `show` and `clear` helpers.
    """
    def __init__(self, menu_buttons: list[MenuButton]) -> None:
        self.menu_buttons = menu_buttons
        self.overlay_entities: list[Entity] = []
        self.font_path = "assets/fonts/PressStart2P-vaV7.ttf"

    def clear(self) -> None:
        """Remove the overlay entities and restore main menu buttons."""
        for entity in self.overlay_entities:
            destroy(entity)
        self.overlay_entities.clear()

        for button in self.menu_buttons:
            button.enabled = True
            button.visible = True

    def show(self, title: str, rows: list[str]) -> None:
        """Display an overlay with a title and a list of rows.

        If rows exceed the visible limit, adds a small scroller input
        handler to navigate the list.
        """
        self.clear()

        for button in self.menu_buttons:
            button.enabled = False
            button.visible = False

        max_visible_rows = 7
        start_index = 0

        title_text = Text(
            parent=camera.ui,
            text=title,
            y=0.1,
            z=-0.10,
            origin=(0, 0),
            font=self.font_path,
            scale=1.15,
            color=colors.rgb(0.729, 0.980, 1.000),
        )
        self.overlay_entities.append(title_text)

        row_start_y = 0.05
        row_step_y = 0.05
        visible_row_entities: list[Text] = []

        if len(rows) > max_visible_rows:
            scroll_hint = Text(
                parent=camera.ui,
                text="SCROLL: WHEEL / UP / DOWN",
                y=-0.28,
                z=-0.10,
                origin=(0, 0),
                font=self.font_path,
                scale=0.45,
                color=colors.rgb(0.729, 0.980, 1.000),
            )
            self.overlay_entities.append(scroll_hint)

        def _refresh_visible_rows() -> None:
            for index, row_text in enumerate(visible_row_entities):
                row_index = start_index + index
                if row_index < len(rows):
                    row_text.text = rows[row_index]
                else:
                    row_text.text = ""

        rows_to_create = min(len(rows), max_visible_rows)
        for index in range(rows_to_create):
            row_text = Text(
                parent=camera.ui,
                text="",
                y=row_start_y - (index * row_step_y),
                z=-0.10,
                origin=(0, 0),
                font=self.font_path,
                scale=0.62,
                color=colors.rgb(1.000, 0.961, 0.620),
            )
            visible_row_entities.append(row_text)
            self.overlay_entities.append(row_text)

        _refresh_visible_rows()

        if len(rows) > max_visible_rows:
            class _OverlayScroller(Entity):
                def input(self, key: str) -> None:
                    nonlocal start_index

                    if key in ("scroll down", "down arrow"):
                        if start_index < len(rows) - max_visible_rows:
                            start_index += 1
                            _refresh_visible_rows()
                    elif key in ("scroll up", "up arrow"):
                        if start_index > 0:
                            start_index -= 1
                            _refresh_visible_rows()

            scroller = _OverlayScroller(parent=camera.ui)
            self.overlay_entities.append(scroller)

        back_button = MenuButton(
            text="BACK",
            on_click=self.clear,
            y=-0.350,
        )
        back_button.z = -0.08
        self.overlay_entities.append(back_button)
