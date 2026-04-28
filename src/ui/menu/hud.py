from collections.abc import Callable
from ursina import Entity, Text, Ursina, Vec2, camera, color, invoke, time
from ursina.curve import linear
from ..components.vhs_effect import VHSEffect


def _fmt_time(total_seconds: float) -> str:
    safe = max(0, int(total_seconds))
    minutes = safe // 60
    seconds = safe % 60
    return f"{minutes:02d}:{seconds:02d}"


class HUDTemplate(Entity):
    def __init__(
        self,
        score: int = 0,
        lives: int = 3,
        level: int = 1,
        remaining_time: float = 120.0,
        countdown: bool = True,
        on_time_finished: Callable[[], None] | None = None,
    ):
        super().__init__(parent=camera.ui)
        self.score = max(0, int(score))
        self.lives = max(0, int(lives))
        self.level = max(1, int(level))
        self.remaining_time = max(0.0, float(remaining_time))
        self.countdown = countdown
        self.on_time_finished = on_time_finished
        self._time_finished_called = self.remaining_time <= 0

        font_path = "assets/fonts/PressStart2P-vaV7.ttf"

        self.score_text = Text(
            parent=self,
            add_to_scene_entities=False,
            text="",
            position=Vec2(-0.86, 0.46),
            color=color.white,
            scale=1.0,
            font=font_path,
        )
        self.time_text = Text(
            parent=self,
            add_to_scene_entities=False,
            text="",
            position=Vec2(0.56, 0.075),
            color=color.white,
            scale=1.0,
            font=font_path,
        )
        self.lives_text = Text(
            parent=self,
            add_to_scene_entities=False,
            text="",
            position=Vec2(-0.86, -0.45),
            color=color.white,
            scale=1.0,
            font=font_path,
        )
        self._lives_base_color = color.white
        self._lives_base_scale = 1.0
        self._lives_pulse_scale = 1.22
        self.level_text = Text(
            parent=self,
            add_to_scene_entities=False,
            text="",
            position=Vec2(0.70, -0.45),
            color=color.white,
            scale=1.0,
            font=font_path,
        )

        VHSEffect(0.5)

        self.refresh()

    def refresh(self):
        self.score_text.text = f"SCORE {self.score:06d}"
        self.time_text.text = f"TIME {_fmt_time(self.remaining_time)}"
        self.lives_text.text = f"LIVES {self.lives}"
        self.level_text.text = f"LVL {self.level:02d}"

    def set_score(self, value: int):
        self.score = max(0, int(value))
        self.refresh()

    def add_score(self, value: int):
        self.set_score(self.score + int(value))

    def set_lives(self, value: int):
        previous_lives = self.lives
        self.lives = max(0, int(value))
        self.refresh()
        if self.lives < previous_lives:
            self._play_life_loss_animation()

    def lose_life(self):
        self.set_lives(self.lives - 1)

    def _play_life_loss_animation(self):
        self.lives_text.scale = self._lives_base_scale
        self.lives_text.color = self._lives_base_color
        self.lives_text.animate_scale(
            self._lives_pulse_scale,
            duration=0.08,
            curve=linear,
        )
        self.lives_text.animate_color(
            color.rgb(1.0, 0.25, 0.25),
            duration=0.08,
            curve=linear,
        )
        invoke(self._restore_lives_text, delay=0.09)

    def _restore_lives_text(self):
        self.lives_text.animate_scale(
            self._lives_base_scale,
            duration=0.18,
            curve=linear,
        )
        self.lives_text.animate_color(
            self._lives_base_color,
            duration=0.18,
            curve=linear,
        )

    def set_level(self, value: int):
        self.level = max(1, int(value))
        self.refresh()

    def set_remaining_time(self, value: float):
        self.remaining_time = max(0.0, float(value))
        if self.remaining_time > 0:
            self._time_finished_called = False
        self.refresh()

    def add_time(self, value: float):
        self.set_remaining_time(self.remaining_time + float(value))

    def update_hud(
        self,
        score: int | None = None,
        lives: int | None = None,
        level: int | None = None,
        remaining_time: float | None = None,
    ):
        if score is not None:
            self.score = max(0, int(score))
        if lives is not None:
            self.lives = max(0, int(lives))
        if level is not None:
            self.level = max(1, int(level))
        if remaining_time is not None:
            self.remaining_time = max(0.0, float(remaining_time))
        if self.remaining_time > 0:
            self._time_finished_called = False
        self.refresh()

    def update(self):
        if self.countdown and self.remaining_time > 0:
            self.remaining_time = max(0.0, self.remaining_time - time.dt)
            if self.remaining_time <= 0 and not self._time_finished_called:
                self._time_finished_called = True
                if self.on_time_finished is not None:
                    self.on_time_finished()
        self.refresh()


class _HUDTester(Entity):
    def __init__(self, hud: HUDTemplate):
        super().__init__()
        self.hud = hud

    def input(self, key):
        if key == 'p':
            self.hud.add_score(100)
        elif key == 'o':
            self.hud.add_score(-100)
        if key == 'l':
            self.hud.lose_life()
        elif key == 'k':
            self.hud.set_lives(self.hud.lives + 1)
        elif key == 'n':
            self.hud.set_level(self.hud.level + 1)
        elif key == 'm':
            self.hud.set_level(self.hud.level - 1)
        elif key == 't':
            self.hud.add_time(15)
        elif key == 'y':
            self.hud.add_time(-15)
        elif key == 'r':
            self.hud.update_hud(
                score=0,
                lives=3,
                level=1,
                remaining_time=120,
            )


def main():
    app = Ursina()
    hud = HUDTemplate(
        score=0,
        lives=3,
        level=1,
        remaining_time=120,
        countdown=True,
    )
    _HUDTester(hud)
    app.run()


if __name__ == "__main__":
    main()
