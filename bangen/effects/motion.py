"""Motion-tier effects."""

from __future__ import annotations

import math

from bangen.effects.base import Effect
from bangen.effects.utils import (
    canvas_to_lines,
    empty_canvas,
    padded_lines,
    place,
    quantized_time,
    signed_noise,
)


def _translate(lines: list[str], dx: int, dy: int) -> list[str]:
    padded, width, height = padded_lines(lines)
    canvas = empty_canvas(width, height)
    for row, line in enumerate(padded):
        for col, char in enumerate(line):
            place(canvas, col + dx, row + dy, char)
    return canvas_to_lines(canvas)


class WaveEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "wave"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        result: list[str] = []
        for row, line in enumerate(padded):
            phase = row * self.config.frequency
            offset = round(
                self.config.amplitude * math.sin(phase + (t * self.config.speed))
            )
            if offset > 0:
                shifted = (" " * offset + line)[:width]
            elif offset < 0:
                shifted = line[-offset:] + (" " * (-offset))
            else:
                shifted = line
            result.append(shifted)
        return result


class VerticalWaveEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "vertical_wave"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        for col in range(width):
            offset = round(
                self.config.amplitude
                * math.sin((col * self.config.frequency) + (t * self.config.speed))
            )
            for row in range(height):
                place(canvas, col, row + offset, padded[row][col])
        return canvas_to_lines(canvas)


class BounceEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "bounce"

    def apply(self, lines: list[str], t: float) -> list[str]:
        dy = round(
            math.sin(t * self.config.speed * math.pi * 1.5) * self.config.amplitude
        )
        return _translate(lines, 0, dy)


class ScrollEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "scroll"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        if width == 0:
            return lines
        offset = int(t * self.config.speed * 10) % width
        return [line[offset:] + line[:offset] for line in padded]


class DriftEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "drift"

    def apply(self, lines: list[str], t: float) -> list[str]:
        dx = int(t * self.config.speed * max(1.0, self.config.amplitude)) % max(
            1, self._base_width or 1
        )
        dy = int(t * self.config.speed * 0.5) % max(1, self._base_height or 1)
        return _translate(lines, dx, dy)


class ShakeEffect(Effect):
    tier = "motion"

    @property
    def name(self) -> str:
        return "shake"

    def apply(self, lines: list[str], t: float) -> list[str]:
        tick = quantized_time(t, self.config.speed, rate=30.0)
        magnitude = max(1, round(self.config.amplitude))
        dx = round(signed_noise(tick, 1.0) * magnitude)
        dy = round(signed_noise(tick, 2.0) * magnitude)
        return _translate(lines, dx, dy)
