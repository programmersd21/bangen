"""Premium Wave-effect"""

from __future__ import annotations

import math

from bangen.effects.base import Effect


class WaveEffect(Effect):
    @property
    def name(self) -> str:
        return "wave"

    def apply(self, lines: list[str], t: float) -> list[str]:
        if not lines:
            return []

        width = max(len(line) for line in lines)
        result: list[str] = []

        for i, line in enumerate(lines):
            padded = line.ljust(width)

            phase = i * self.config.frequency
            offset = round(
                self.config.amplitude * math.sin(phase + t * self.config.speed)
            )

            if offset > 0:
                shifted = (" " * offset + padded)[:width]
            elif offset < 0:
                shifted = padded[-offset:] + " " * (-offset)
            else:
                shifted = padded

            result.append(shifted[:width])

        return result