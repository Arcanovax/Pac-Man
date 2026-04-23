from ursina import (
    Entity,
    Ursina,
    camera,
    color as colors,
    destroy,
    window,
)

from ...logger import Logger
from ...render.main import run_main_maze
from ..components import MenuButton, MenuLogo, PacmanBackground, VHSEffect
from .end_screen import show_game_over_screen, show_victory_screen
from .highscores_menu import show_highscores_menu  # type: ignore
from .instructions_menu import show_instructions_menu  # type: ignore
from .overlay_menu import OverlayMenuManager  # type: ignore


def run_main_menu(config) -> None:
    app = Ursina(
        borderless=False,
        title="Pac-Man",
        color=colors.rgb(0.110, 0.133, 0.227),
        development_mode=False
    )

    window.exit_button.visible = False
    window.fps_counter.enabled = False

    _build_menu_ui(app, config)
    app.run()


def _build_menu_ui(app: Ursina, config) -> None:
    highscore = getattr(config, "highscore", config)
    highscore_filename = getattr(
        config,
        "highscore_filename",
        "highscore.json",
    )
    can_start_game = hasattr(config, "width") and hasattr(config, "height")

    menu_entities: list[Entity] = []
    menu_entities.append(PacmanBackground())
    menu_entities.extend(_build_retro_frame())
    menu_entities.append(MenuLogo(y=0.300))
    menu_entities.append(VHSEffect(intensity=0.50))

    menu_buttons: list[MenuButton] = []
    overlay = OverlayMenuManager(menu_buttons)
    game_session = None

    def _set_menu_visible(visible: bool) -> None:
        for entity in menu_entities:
            entity.enabled = visible
            entity.visible = visible

        for button in menu_buttons:
            button.enabled = visible
            button.visible = visible

    def _back_to_menu() -> None:
        nonlocal game_session
        if game_session is not None:
            game_session.close()
            game_session = None
        _set_menu_visible(True)

    def _on_game_over(final_score: int) -> None:
        show_game_over_screen(
            final_score=final_score,
            highscore=highscore,
            on_close=_back_to_menu,
            highscore_filename=highscore_filename,
        )

    def _on_victory(final_score: int) -> None:
        show_victory_screen(
            final_score=final_score,
            highscore=highscore,
            on_close=_back_to_menu,
            highscore_filename=highscore_filename,
        )

    def _play() -> None:
        nonlocal game_session
        if not can_start_game:
            Logger.warning("Cannot start game from sample highscore mode")
            return

        overlay.clear()
        _set_menu_visible(False)
        Logger.debug("Start game clicked from main menu")
        game_session = run_main_maze(
            config=config,
            on_game_over=_on_game_over,
            on_victory=_on_victory,
            app=app,
        )

    def _highscores() -> None:
        show_highscores_menu(highscore, overlay)

    def _instructions() -> None:
        show_instructions_menu(overlay)

    def _quit() -> None:
        Logger.debug("Exit clicked from main menu")
        if game_session is not None:
            game_session.close()
        destroy(camera.ui)
        app.userExit()

    menu_buttons.append(MenuButton(text="START GAME", on_click=_play, y=0.025))
    menu_buttons.append(
        MenuButton(
            text="VIEW HIGH SCORES",
            on_click=_highscores,
            y=-0.085,
        )
    )
    menu_buttons.append(
        MenuButton(
            text="INSTRUCTIONS",
            on_click=_instructions,
            y=-0.195,
        )
    )
    menu_buttons.append(MenuButton(text="EXIT", on_click=_quit, y=-0.305))


def _build_retro_frame() -> list[Entity]:
    frame_entities: list[Entity] = []

    frame_entities.append(Entity(
        parent=camera.ui,
        model="quad",
        y=-0.10,
        z=0.04,
        scale=(0.78, 0.70),
        color=colors.rgba(0.051, 0.078, 0.141, 0.745),
    ))

    frame_entities.append(Entity(
        parent=camera.ui,
        model="quad",
        y=-0.10,
        z=0.03,
        scale=(0.756, 0.676),
        color=colors.rgba(0.020, 0.031, 0.063, 0.608),
    ))

    frame_entities.append(Entity(
        parent=camera.ui,
        model="quad",
        y=0.17,
        z=0.02,
        scale=(0.70, 0.008),
        color=colors.rgba(0.322, 0.824, 1.000, 0.569),
    ))

    return frame_entities


if __name__ == "__main__":
    class _TmpConfig:
        highscore = [
            {"name": "Player1", "score": 1000},
            {"name": "Player2", "score": 800},
            {"name": "Player3", "score": 600},
        ]
        highscore_filename = "highscore.json"

    run_main_menu(_TmpConfig())
