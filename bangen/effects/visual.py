"""Visual-tier effects."""

from __future__ import annotations

import math

from bangen.effects.base import Effect, RasterLayer
from bangen.effects.utils import blend_colors, clamp, hash_noise, scale_color, shift_hue


class GradientShiftEffect(Effect):
    tier = "visual"

    @property
    def name(self) -> str:
        return "gradient_shift"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def transform_gradient_position(
        self,
        position: float,
        *,
        t: float,
        row: int,
        col: int,
        line_length: int,
        line_count: int,
        char: str,
        lines: list[str],
    ) -> float:
        del row, col, line_length, line_count, char, lines
        return (position + (t * self.config.speed * 0.12)) % 1.0


class PulseEffect(Effect):
    tier = "visual"

    def __init__(
        self,
        config=None,
        min_brightness: float = 0.35,
        max_brightness: float = 1.0,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness

    @property
    def name(self) -> str:
        return "pulse"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def brightness(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        del row, col, char, lines
        phase = (math.sin(t * self.config.speed * math.pi) + 1.0) / 2.0
        return self.min_brightness + phase * (
            self.max_brightness - self.min_brightness
        )


class RainbowCycleEffect(Effect):
    tier = "visual"

    @property
    def name(self) -> str:
        return "rainbow_cycle"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def colorize(
        self,
        color,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ):
        del char, lines
        amount = (t * self.config.speed * 0.08) + ((row + col) * 0.006)
        return shift_hue(color, amount)


class GlowEffect(Effect):
    tier = "visual"

    @property
    def name(self) -> str:
        return "glow"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def colorize(
        self,
        color,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ):
        del t, row, col, char, lines
        return scale_color(color, 1.18)

    def raster_layers(
        self,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
        color,
        opacity: float,
    ) -> tuple[RasterLayer, ...]:
        del t, row, col, lines
        if char == " " or opacity <= 0.01:
            return ()
        bloom = blend_colors(color, (255, 255, 255), 0.18)
        return (
            RasterLayer(dx=-1, dy=0, color=bloom, alpha=0.18),
            RasterLayer(dx=1, dy=0, color=bloom, alpha=0.18),
            RasterLayer(dx=0, dy=-1, color=bloom, alpha=0.14),
            RasterLayer(dx=0, dy=1, color=bloom, alpha=0.14),
        )


class FlickerEffect(Effect):
    tier = "visual"

    @property
    def name(self) -> str:
        return "flicker"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def brightness(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        del row, col, char, lines
        frame = math.floor(t * self.config.speed * 28.0)
        noise = hash_noise(frame, self.config.amplitude, 7.0)
        if noise > 0.92:
            return 0.25 + (hash_noise(frame, 13.0) * 0.35)
        return 0.82 + (noise * 0.18)


class ScanlineEffect(Effect):
    tier = "visual"

    @property
    def name(self) -> str:
        return "scanline"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def brightness(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        del col, char, lines
        phase = int(t * self.config.speed * 10.0)
        return 0.55 if (row + phase) % 2 else 0.95


class LoopPulseEffect(Effect):
    tier = "temporal"

    @property
    def name(self) -> str:
        return "loop_pulse"

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def brightness(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        del row, col, char, lines
        phase = (t * self.config.speed) % 1.0
        if phase < 0.2:
            envelope = phase / 0.2
        elif phase < 0.55:
            envelope = 1.0 - ((phase - 0.2) / 0.35)
        else:
            envelope = 0.0
        return 0.45 + (clamp(envelope) * 0.55)
