from ...logger import Logger
from .overlay_menu import OverlayMenuManager


def show_highscores_menu(
    highscore: list[dict[str, int | str]],
    overlay: OverlayMenuManager,
) -> None:
    """Prepare and display the highscores overlay.

    Sorts and formats the top scores then delegates rendering to the
    provided `overlay` manager.
    """

    rows: list[str] = []

    try:
        sorted_scores = sorted(
            highscore,
            key=lambda item: int(item.get("score", 0)),
            reverse=True,
        )[:10]
        rows = [
            (
                f"{index + 1}. "
                f"{item.get('name', 'UNKNOWN')}  "
                f"{item.get('score', 0)}"
            )
            for index, item in enumerate(sorted_scores)
        ]
    except Exception as error:
        Logger.warning(f"Failed to load highscores: {error}")

    if not rows:
        rows = ["No high score available."]

    overlay.show("HIGH SCORES", rows)
    Logger.debug("High scores opened from main menu")
