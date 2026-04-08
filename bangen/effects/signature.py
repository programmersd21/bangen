"""Signature and composite effects."""

from __future__ import annotations

import math

from bangen.effects.base import Effect, RasterLayer
from bangen.effects.utils import (
    blend_colors,
    canvas_to_lines,
    empty_canvas,
    hash_noise,
    padded_lines,
    palette_color,
    place,
    quantized_time,
    scale_color,
    signed_noise,
)

_MATRIX_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$#@&*+-"
_FIRE_CHARS = " .:^*#"


class MatrixRainEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "matrix_rain"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        trail = max(3, int(4 + self.config.amplitude * 2))
        tick = quantized_time(t, self.config.speed, rate=18.0)

        for col in range(width):
            head = int((tick + (col * 3)) % (height + trail)) - trail
            for row in range(height):
                if padded[row][col] == " ":
                    continue
                if row <= head and row >= head - trail:
                    index = int(hash_noise(row, col, tick, 31.0) * len(_MATRIX_CHARS))
                    place(canvas, col, row, _MATRIX_CHARS[index % len(_MATRIX_CHARS)])
        return canvas_to_lines(canvas)

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
        del color, char, lines
        brightness = 0.45 + (
            hash_noise(row, col, quantized_time(t, self.config.speed), 9.0) * 0.45
        )
        return scale_color((90, 255, 120), brightness)


class FireEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "fire"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        tick = quantized_time(t, self.config.speed, rate=20.0)
        for row, line in enumerate(padded):
            for col, char in enumerate(line):
                if char == " ":
                    continue
                sway = math.sin(
                    (col * self.config.frequency * 0.6) + (t * self.config.speed * 1.6)
                )
                dx = round(sway * (self.config.amplitude * 0.8))
                dy = -round(hash_noise(tick, row, col, 5.0) * self.config.amplitude)
                target_row = max(0, row + dy)
                target_col = col + dx
                fire_index = min(
                    len(_FIRE_CHARS) - 1,
                    int(hash_noise(tick, row, col, 11.0) * len(_FIRE_CHARS)),
                )
                place(
                    canvas,
                    target_col,
                    target_row,
                    _FIRE_CHARS[fire_index] if row > 0 else char,
                )
                place(canvas, target_col, target_row + 1, char)
        return canvas_to_lines(canvas)

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
        del color, char
        heat = 1.0 - (row / max(1, len(lines) - 1))
        flicker = hash_noise(row, col, quantized_time(t, self.config.speed), 17.0)
        return palette_color(
            [(120, 0, 0), (255, 80, 0), (255, 220, 80), (255, 255, 180)],
            min(1.0, (heat * 0.7) + (flicker * 0.3)),
        )


class ElectricEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "electric"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        tick = quantized_time(t, self.config.speed, rate=42.0)
        for row, line in enumerate(padded):
            for col, char in enumerate(line):
                if char == " ":
                    continue
                dx = round(signed_noise(tick, row, col, 7.0) * self.config.amplitude)
                dy = round(
                    signed_noise(tick, row, col, 13.0) * (self.config.amplitude * 0.5)
                )
                place(canvas, col + dx, row + dy, char)
        return canvas_to_lines(canvas)

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
        burst = hash_noise(quantized_time(t, self.config.speed, 36.0), 5.0)
        return 0.75 + (0.75 if burst > 0.86 else burst * 0.3)

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
        return blend_colors(color, (220, 245, 255), 0.45)

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
        return (
            RasterLayer(dx=-1, dy=0, color=(80, 220, 255), alpha=0.24),
            RasterLayer(dx=1, dy=0, color=(255, 255, 255), alpha=0.18),
        )


class VHSGlitchEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "vhs_glitch"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        tick = quantized_time(t, self.config.speed, rate=20.0)
        result: list[str] = []
        for row, line in enumerate(padded):
            row_jump = round(
                signed_noise(tick, row, 3.0)
                * self.config.amplitude
                * (2.4 if hash_noise(tick, row, 4.0) > 0.82 else 0.6)
            )
            if row_jump > 0:
                result.append((" " * row_jump + line)[:width])
            elif row_jump < 0:
                result.append(line[-row_jump:] + (" " * (-row_jump)))
            else:
                result.append(line)
        return result

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
        phase = int(t * self.config.speed * 12)
        return 0.62 if (row + phase) % 2 else 0.96

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
        return blend_colors(color, (220, 180, 255), 0.2)

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
        del row, col, lines
        if char == " " or opacity <= 0.01:
            return ()
        shift = 1 if math.sin(t * self.config.speed * 2.4) >= 0 else -1
        return (
            RasterLayer(dx=shift, dy=0, color=(255, 70, 120), alpha=0.22),
            RasterLayer(dx=-shift, dy=0, color=(80, 220, 255), alpha=0.22),
        )


class NeonSignEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "neon_sign"

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
        pulse = (math.sin(t * self.config.speed * math.pi * 1.25) + 1.0) / 2.0
        flicker = hash_noise(quantized_time(t, self.config.speed, 32.0), 7.0)
        dip = 0.25 if flicker > 0.94 else 0.0
        return 0.68 + (pulse * 0.35) - dip

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
        return blend_colors(color, (255, 255, 255), 0.15)

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
        bright = blend_colors(color, (255, 255, 255), 0.2)
        return (
            RasterLayer(dx=-1, dy=0, color=bright, alpha=0.22),
            RasterLayer(dx=1, dy=0, color=bright, alpha=0.22),
            RasterLayer(dx=0, dy=-1, color=bright, alpha=0.18),
            RasterLayer(dx=0, dy=1, color=bright, alpha=0.18),
        )


class WaveInterferenceEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "wave_interference"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        result: list[str] = []
        for row, line in enumerate(padded):
            primary = math.sin((row * self.config.frequency) + (t * self.config.speed))
            secondary = math.sin(
                (row * self.config.frequency * 1.73) - (t * self.config.speed * 1.37)
            )
            offset = round((primary + secondary) * self.config.amplitude)
            if offset > 0:
                result.append((" " * offset + line)[:width])
            elif offset < 0:
                result.append(line[-offset:] + (" " * (-offset)))
            else:
                result.append(line)
        return result
