import math

from ursina import Entity, Sprite, camera, color as colors, time


class MenuLogo(Entity):
    """Logo entity used in menus to display and animate the game's logo.

    Provides a subtle bobbing animation in `update` to give life to the
    static logo graphic.
    """
    def __init__(self, y: float = 0.32) -> None:
        super().__init__(parent=camera.ui)

        logo_path = "assets/logo/pacman.png"
        self._base_y = y
        self._t = 0.0

        Sprite(
            parent=self,
            texture=str(logo_path),
            y=y - 0.003,
            z=0.01,
            scale=(0.005, 0.005),
            color=colors.rgba(0.020, 0.078, 0.161, 0.706),
        )

        self._logo = Sprite(
            parent=self,
            texture=str(logo_path),
            y=y,
            z=0.0,
            scale=(0.031, 0.031),
        )

    def update(self) -> None:
        """Animate the logo with a small sinusoidal vertical offset."""
        self._t += time.dt
        self._logo.y = self._base_y + (math.sin(self._t * 2.0) * 0.0009)
