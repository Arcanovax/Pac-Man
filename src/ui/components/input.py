from ursina import InputField, Entity, Text, color as colors, time


class MenuInput(InputField):
    """Text input field styled for menu UIs.

    Extends Ursina's `InputField` with a retro look, label support, and a
    blinking cursor implementation constrained by a character limit.
    """
    def __init__(
        self,
        default_value: str = "",
        label: str = "",
        y: float = 0,
        width: float = 0.38,
        height: float = 0.080,
        max_lines: int = 1,
        character_limit: int = 24,
    ) -> None:
        Text.default_monospace_font = "assets/fonts/PressStart2P-vaV7.ttf"
        self._base_width = width
        self._base_height = height
        self._aspect_compensation = width / max(height, 0.001)
        self._left_padding = -0.43
        self._right_padding = 0.43
        self._font_path = "assets/fonts/PressStart2P-vaV7.ttf"

        self._base_text_color = colors.rgb(1.000, 0.961, 0.620)
        self._active_text_color = colors.rgb(0.729, 0.980, 1.000)
        self._base_color = colors.rgb(0.071, 0.098, 0.169)
        self._active_color = colors.rgb(0.110, 0.161, 0.251)
        self._base_frame_color = colors.rgb(0.290, 0.545, 0.800)
        self._active_frame_color = colors.rgb(0.420, 0.725, 1.000)

        if character_limit > 21:
            character_limit = 21

        super().__init__(
            default_value=default_value,
            max_lines=max_lines,
            character_limit=character_limit,
            y=y,
            scale=(width, height),
            color=self._base_color,
            limit_content_to=(
                "abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                " 0123456789"
            )
        )

        self.character_limit = character_limit
        self.text_field.font = self._font_path
        self.text_field.color = self._base_text_color
        self.text_field.origin = (-0.5, 0)
        self.text_field.x = self._left_padding
        self.text_field.y = -0.01
        self.text_field.scale = (1.65, 1.65 * self._aspect_compensation)
        self.text_field.z = -0.1

        if label:
            self._label_entity = Text(
                parent=self,
                text=label,
                x=0,
                y=0.16,
                z=-0.1,
                origin=(0, 0),
                font=self._font_path,
                scale=(1.25, 1.25 * self._aspect_compensation),
                color=self._base_text_color,
            )
        else:
            self._label_entity = None

        self._frame = Entity(
            parent=self,
            model="quad",
            x=0, y=0, z=0.03,
            scale=(1.04, 1.16),
            color=self._base_frame_color,
            ignore=True,
        )

        self._depth = Entity(
            parent=self,
            model="quad",
            x=0, y=-0.065, z=0.015,
            scale=(0.98, 0.16),
            color=colors.rgb(0.027, 0.039, 0.063),
            ignore=True,
        )

        self._scanlines: list[Entity] = []
        num_lines = 6
        for i in range(num_lines):
            ypos = -0.38 + i * (0.76 / (num_lines - 1))
            line = Entity(
                parent=self,
                model="quad",
                x=0,
                y=ypos,
                z=-0.02,
                scale=(0.96, 0.045),
                color=colors.rgba(0, 0, 0, 0.12),
                ignore=True,
            )
            self._scanlines.append(line)

        self._top_glow = Entity(
            parent=self,
            model="quad",
            x=0, y=0.28, z=0.02,
            scale=(0.72, 0.10),
            color=colors.rgba(0.729, 0.980, 1.000, 0.18),
            ignore=True,
        )

        self._cursor = Text(
            parent=self,
            text="_",
            x=0, y=-0.175, z=-0.5,
            origin=(0, 0),
            font=self._font_path,
            scale=(1.85, 1.85 * self._aspect_compensation),
            color=self._active_text_color,
            enabled=False,
        )

        self._cursor_blink_time = 0
        self._cursor_visible = True

    def input(self, key: str) -> None:
        """Process input events and manage active styling.

        Activates the input when clicked or tabbed into and deactivates
        when Escape is pressed.
        """
        super().input(key)

        if not self.active and key in ('left mouse down', 'tab'):
            self._activate_style()
        elif self.active and key == 'escape':
            self._deactivate_style()

    def _activate_style(self) -> None:
        """Apply active visuals when the input gains focus."""
        self.text_field.color = self._active_text_color
        self.color = self._active_color
        self._frame.color = self._active_frame_color
        self._cursor.enabled = True
        if self._label_entity:
            self._label_entity.color = self._active_text_color

    def _deactivate_style(self) -> None:
        """Restore base visuals when the input loses focus."""
        self.text_field.color = self._base_text_color
        self.color = self._base_color
        self._frame.color = self._base_frame_color
        self._cursor.enabled = False
        if self._label_entity:
            self._label_entity.color = self._base_text_color

    def update(self) -> None:
        """Update cursor blink and clamp cursor position to input width."""
        if (len(self.text) >= self.character_limit):
            self._cursor.enabled = False
        else:
            self._cursor.enabled = True
        if (
            self.active
            and self._cursor.enabled
            and len(self.text) < self.character_limit
        ):
            self._cursor_blink_time += time.dt
            if self._cursor_blink_time >= 0.5:
                self._cursor_visible = not self._cursor_visible
                self._cursor.alpha = 1.0 if self._cursor_visible else 0.0
                self._cursor_blink_time = 0

            text_width = len(self.text) * 0.041
            cursor_x = self._left_padding + text_width + 0.02
            self._cursor.x = min(cursor_x, self._right_padding)

    def on_mouse_enter(self) -> None:
        """Visual hint when mouse hovers over the input field."""
        if not self.active:
            self._frame.color = self._active_frame_color
            self.scale = (self._base_width * 1.01, self._base_height * 1.01)

    def on_mouse_exit(self) -> None:
        """Restore visuals when mouse leaves the input field area."""
        if not self.active:
            self._frame.color = self._base_frame_color
            self.scale = (self._base_width, self._base_height)


def main() -> None:
    from ursina import Ursina, camera

    app = Ursina()
    camera.orthographic = True
    camera.fov = 2
    MenuInput(
        label="PSEUDO",
        y=0.2,
        default_value="",
        character_limit=21,
    )

    app.run()


if __name__ == "__main__":
    main()
