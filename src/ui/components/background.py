import math

from ursina import Entity, camera, color as colors, time


class PacmanBackground(Entity):
    """Background composition for menu screens.

    Draws layered colored bands and separators that animate subtly to
    provide a retro styled backdrop for menus.
    """
    def __init__(self) -> None:
        super().__init__(parent=camera.ui)

        self._t = 0.0
        self._blue_lines: list[Entity] = []
        self._blue_line_base_y: list[float] = []

        Entity(
            parent=self,
            model="quad",
            color=colors.rgb(0.043, 0.071, 0.133),
            scale=(2.4, 1.4),
            z=2,
        )

        Entity(
            parent=self,
            model="quad",
            color=colors.rgba(0.078, 0.161, 0.239, 0.188),
            y=0.24,
            scale=(2.4, 0.62),
            z=1.95,
        )

        self._create_blue_bands()
        self._create_blue_separators()

        self._sweep_band = Entity(
            parent=self,
            model="quad",
            y=0.72,
            z=1.88,
            scale=(2.4, 0.048),
            color=colors.rgba(0.380, 0.820, 1.000, 0.090),
        )

    def update(self) -> None:
        """Advance background animation state each frame."""
        self._t += time.dt
        self._animate_blue_bands()

    def _create_blue_bands(self) -> None:
        """Create the repeated blue band entities used in the background."""
        for i in range(34):
            base_y = 0.66 - (i * 0.041)
            line = Entity(
                parent=self,
                model="quad",
                y=base_y,
                z=1.90,
                scale=(2.4, 0.0036),
                color=colors.rgba(
                    0.160,
                    0.490,
                    0.690,
                    0.090 + ((i % 3) * 0.016),
                ),
            )
            self._blue_lines.append(line)
            self._blue_line_base_y.append(base_y)

    def _create_blue_separators(self) -> None:
        """Create horizontal separator lines in the background."""
        for y in (0.13, -0.09):
            Entity(
                parent=self,
                model="quad",
                y=y,
                z=1.84,
                scale=(2.4, 0.008),
                color=colors.rgba(0.298, 0.820, 1.000, 0.275),
            )

    def _animate_blue_bands(self) -> None:
        """Animate the sweep band and drifting blue lines over time."""
        self._sweep_band.y = 0.74 - ((self._t * 0.35) % 1.52)
        pulse_alpha = 0.085 + (math.sin(self._t * 10.0) * 0.020)
        self._sweep_band.color = colors.rgba(0.380, 0.820, 1.000, pulse_alpha)

        drift = (self._t * 0.011) % 1.394
        for i, line in enumerate(self._blue_lines):
            y = self._blue_line_base_y[i] - drift
            if y < -0.74:
                y += 1.394
            line.y = y
