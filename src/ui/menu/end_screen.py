import json
from collections.abc import Callable

from ursina import (
    Entity,
    Text,
    Ursina,
    application,
    camera,
    color as colors,
    destroy,
)

from ...logger import Logger
from ..components import MenuButton, VHSEffect
from ..components.input import MenuInput
from ..components.background import PacmanBackground


def _normalize_player_name(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        return "PLAYER"
    return cleaned[:21]


def _save_highscore(
    highscore: list[dict[str, int | str]],
    player_name: str,
    final_score: int,
    highscore_filename: str,
) -> list[dict[str, int | str]]:
    """Append a new score entry and persist the top 10 list.

    Normalizes the player name, inserts the new score into the list,
    sorts by score descending, trims to the top 10 and writes the
    result to `highscore_filename`.

    Returns the updated highscore list.
    """

    entry: dict[str, int | str] = {
        "name": _normalize_player_name(player_name),
        "score": max(0, int(final_score)),
    }

    updated = list(highscore)
    updated.append(entry)
    updated = sorted(
        updated,
        key=lambda item: int(item.get("score", 0)),
        reverse=True,
    )
    updated = updated[:10]

    highscore.clear()
    highscore.extend(updated)

    try:
        with open(highscore_filename, "w", encoding="utf-8") as score_file:
            json.dump(highscore, score_file, ensure_ascii=False, indent=2)
    except Exception as error:
        Logger.warning(f"Failed to save highscores: {error}")

    return highscore


def _show_end_screen(
    title: str,
    subtitle: str,
    final_score: int,
    highscore: list[dict[str, int | str]],
    highscore_filename: str,
    on_close: Callable[[], None] | None,
) -> None:
    """Render an end-of-game UI panel allowing the player to save score.

    Displays title, subtitle, final score and an input to enter a name.
    Provides buttons to save the score or continue/close the screen.
    """

    PacmanBackground()
    ui_entities: list[Entity] = []
    saved_once = False
    font_path = "assets/fonts/PressStart2P-vaV7.ttf"

    panel = Entity(
        parent=camera.ui,
        model="quad",
        scale=(0.82, 0.76),
        y=-0.02,
        z=1.0,
        color=colors.rgba(0.051, 0.078, 0.141, 0.90),
    )
    ui_entities.append(panel)

    title_text = Text(
        parent=camera.ui,
        text=title,
        y=0.25,
        z=-0.05,
        origin=(0, 0),
        font=font_path,
        scale=1.3,
        color=colors.rgb(0.729, 0.980, 1.000),
    )
    ui_entities.append(title_text)

    subtitle_text = Text(
        parent=camera.ui,
        text=subtitle,
        y=0.17,
        z=-0.05,
        origin=(0, 0),
        font=font_path,
        scale=0.62,
        color=colors.rgb(1.000, 0.961, 0.620),
    )
    ui_entities.append(subtitle_text)

    score_text = Text(
        parent=camera.ui,
        text=f"FINAL SCORE: {max(0, int(final_score))}",
        y=0.07,
        z=-0.05,
        origin=(0, 0),
        font=font_path,
        scale=0.82,
        color=colors.rgb(1.000, 0.961, 0.620),
    )
    ui_entities.append(score_text)

    prompt_text = Text(
        parent=camera.ui,
        text="ENTER YOUR NAME",
        y=-0.02,
        z=-0.05,
        origin=(0, 0),
        font=font_path,
        scale=0.55,
        color=colors.rgb(0.729, 0.980, 1.000),
    )
    ui_entities.append(prompt_text)

    status_text = Text(
        parent=camera.ui,
        text="",
        y=-0.2,
        z=-0.05,
        origin=(0, 0),
        font=font_path,
        scale=0.45,
        color=colors.rgb(0.729, 0.980, 1.000),
    )
    ui_entities.append(status_text)

    name_input = MenuInput(
        label="NAME",
        y=-0.12,
        default_value="",
        character_limit=21,
    )
    ui_entities.append(name_input)

    def _close_screen() -> None:
        for entity in ui_entities:
            destroy(entity)
        if on_close is not None:
            on_close()

    def _save_score() -> None:
        nonlocal saved_once

        if saved_once:
            status_text.text = "ALREADY SAVED"
            return

        _save_highscore(
            highscore=highscore,
            player_name=name_input.text,
            final_score=final_score,
            highscore_filename=highscore_filename,
        )
        saved_once = True
        status_text.text = "SCORE SAVED"
        Logger.debug("End screen score saved")

    save_button = MenuButton(
        text="SAVE SCORE",
        on_click=_save_score,
        y=-0.3,
    )
    save_button.z = -0.03
    save_button.x = 0.2
    ui_entities.append(save_button)

    continue_button = MenuButton(
        text="CONTINUE",
        on_click=_close_screen,
        y=-0.3,
    )
    continue_button.z = -0.03
    continue_button.x = -0.2
    ui_entities.append(continue_button)

    VHSEffect(0.4)


def show_game_over_screen(
    final_score: int,
    highscore: list[dict[str, int | str]],
    on_close: Callable[[], None] | None = None,
    highscore_filename: str = "highscore.json",
) -> None:
    """Convenience wrapper to show the 'game over' end screen."""
    _show_end_screen(
        title="GAME OVER",
        subtitle="TRY AGAIN NEXT RUN",
        final_score=final_score,
        highscore=highscore,
        highscore_filename=highscore_filename,
        on_close=on_close,
    )


def show_victory_screen(
    final_score: int,
    highscore: list[dict[str, int | str]],
    on_close: Callable[[], None] | None = None,
    highscore_filename: str = "highscore.json",
) -> None:
    """Convenience wrapper to show the victory end screen."""
    _show_end_screen(
        title="VICTORY",
        subtitle="CONGRATULATIONS! YOU WON!",
        final_score=final_score,
        highscore=highscore,
        highscore_filename=highscore_filename,
        on_close=on_close,
    )


def _run_test_main() -> None:
    """Run a standalone test harness that displays the end screens.

    This helper is intended for local testing and demoing the UI only.
    """

    app = Ursina(
        borderless=False,
        title="Pac-Man End Screen Test",
        development_mode=False,
    )

    highscore: list[dict[str, int | str]] = [
        {"name": "PLAYER1", "score": 10000},
        {"name": "PLAYER2", "score": 7500},
    ]
    launcher_entities: list[Entity] = []

    def _set_launcher_visible(visible: bool) -> None:
        for entity in launcher_entities:
            entity.enabled = visible
            entity.visible = visible

    def _back_to_launcher() -> None:
        _set_launcher_visible(True)

    def _open_game_over() -> None:
        _set_launcher_visible(False)
        show_game_over_screen(
            final_score=4321,
            highscore=highscore,
            on_close=_back_to_launcher,
            highscore_filename="highscore.json",
        )

    def _open_victory() -> None:
        _set_launcher_visible(False)
        show_victory_screen(
            final_score=9876,
            highscore=highscore,
            on_close=_back_to_launcher,
            highscore_filename="highscore.json",
        )

    title = Text(
        parent=camera.ui,
        text="END MENU TEST",
        y=0.28,
        scale=1.2,
        origin=(0, 0),
        font="assets/fonts/PressStart2P-vaV7.ttf",
        color=colors.rgb(0.729, 0.980, 1.000),
    )
    launcher_entities.append(title)

    launcher_entities.append(
        MenuButton(text="TEST GAME OVER", on_click=_open_game_over, y=0.06)
    )
    launcher_entities.append(
        MenuButton(text="TEST VICTORY", on_click=_open_victory, y=-0.06)
    )
    launcher_entities.append(
        MenuButton(text="QUIT", on_click=application.quit, y=-0.18)
    )

    app.run()


if __name__ == "__main__":
    _run_test_main()
