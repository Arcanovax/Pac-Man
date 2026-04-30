from ...logger import Logger
from .overlay_menu import OverlayMenuManager


def show_instructions_menu(overlay: OverlayMenuManager) -> None:
    """Open the instructions overlay explaining basic controls and goals."""
    overlay.show(
        "INSTRUCTIONS",
        [
            "- Move with W, A, S, D",
            "- Eat pac-gums to score",
            "- Avoid ghosts",
            "- Grab power pellets",
            "- Clear level to win",
        ],
    )
    Logger.debug("Instructions opened from main menu")
