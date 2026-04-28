from __future__ import annotations

import math
import random

from ursina import Entity, camera, color as colors, time


class VHSEffect(Entity):
    def __init__(self, intensity: float = 1.0) -> None:
        super().__init__(parent=camera.ui)

        self._intensity = max(0.1, intensity)
        self._t = random.random() * 10.0
        self._jitter_timer = 0.0
        self._jitter_interval = 0.08
        self._jitter_strength = 0.0018 * self._intensity
        self._scanline_bases: list[float] = []
        self._overlay_alpha = max(0.004, 0.020 * self._intensity)
        self._bleed_alpha = max(0.004, 0.016 * self._intensity)
        self._scanline_alpha = max(0.006, 0.035 * self._intensity)
        self._noise_min_alpha = max(0.006, 0.014 * self._intensity)
        self._noise_max_alpha = max(0.010, 0.040 * self._intensity)

        Entity(
            parent=self,
            add_to_scene_entities=False,
            model="quad",
            scale=(2.08, 1.22),
            z=-0.86,
            color=colors.rgba(0.063, 0.102, 0.141, self._overlay_alpha),
        )

        self._red_bleed = Entity(
            parent=self,
            add_to_scene_entities=False,
            model="quad",
            x=0.0015,
            scale=(2.08, 1.22),
            z=-0.85,
            color=colors.rgba(1.000, 0.216, 0.216, self._bleed_alpha),
        )

        self._blue_bleed = Entity(
            parent=self,
            add_to_scene_entities=False,
            model="quad",
            x=-0.0015,
            scale=(2.08, 1.22),
            z=-0.85,
            color=colors.rgba(0.251, 0.780, 1.000, self._bleed_alpha),
        )

        self._noise_band = Entity(
            parent=self,
            add_to_scene_entities=False,
            model="quad",
            y=0.62,
            scale=(2.12, 0.055),
            z=-0.84,
            color=colors.rgba(0.824, 0.922, 1.000, self._noise_max_alpha),
        )

        self._scanlines = self._create_scanlines()

    def _create_scanlines(self) -> list[Entity]:
        lines: list[Entity] = []
        step = 0.034

        for i in range(40):
            y = 0.68 - (i * step)
            line = Entity(
                parent=self,
                add_to_scene_entities=False,
                model="quad",
                y=y,
                scale=(2.12, 0.0026),
                z=-0.83,
                color=colors.rgba(0.055, 0.118, 0.157, self._scanline_alpha),
            )
            lines.append(line)
            self._scanline_bases.append(y)

        return lines

    def update(self) -> None:
        self._t += time.dt
        self._jitter_timer += time.dt

        if self._jitter_timer >= self._jitter_interval:
            self._jitter_timer = 0.0
            self.x = random.uniform(
                -self._jitter_strength,
                self._jitter_strength,
            )

        band_progress = (self._t * 0.42) % 1.5
        self._noise_band.y = 0.74 - band_progress

        flicker = self._noise_max_alpha + (math.sin(self._t * 22.0) * 0.004)
        flicker += random.uniform(-0.003, 0.003)
        alpha = max(self._noise_min_alpha, min(self._noise_max_alpha, flicker))
        self._noise_band.color = colors.rgba(0.824, 0.922, 1.000, alpha)

        shift = math.sin(self._t * 3.5) * 0.0015 * self._intensity
        self._red_bleed.x = 0.0015 + shift
        self._blue_bleed.x = -0.0015 - shift

        scan_offset = (self._t * 0.02) % 0.034
        for i, line in enumerate(self._scanlines):
            line.y = self._scanline_bases[i] + scan_offset
