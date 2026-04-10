"""Temporal-tier effects."""

from __future__ import annotations

from bangen.effects.base import Effect
from bangen.effects.utils import clamp


class TypewriterEffect(Effect):
    tier = "temporal"

    def __init__(
        self,
        config=None,
        chars_per_second: float = 50.0,
        loop: bool = True,
        pause: float = 0.5,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.chars_per_second = chars_per_second
        self.loop = loop
        self.pause = pause

    @property
    def name(self) -> str:
        return "typewriter"

    def precompute(self, banner) -> None:
        super().precompute(banner)
        self._full_text = "\n".join(self._base_lines)
        self._total_chars = len(self._full_text)

    def apply(self, lines: list[str], t: float) -> list[str]:
        if self._total_chars == 0:
            return lines

        speed = max(self.config.speed, 0.1)
        t = t * speed

        typing_time = self._total_chars / self.chars_per_second
        cycle_time = typing_time + self.pause

        if self.loop:
            t = t % cycle_time
        else:
            t = min(t, typing_time)

        revealed = min(self._total_chars, int(t * self.chars_per_second))

        visible = self._full_text[:revealed].split("\n")

        result: list[str] = []
        for row, line in enumerate(lines):
            if row < len(visible):
                current = visible[row]
                result.append(current + " " * max(0, len(line) - len(current)))
            else:
                result.append(" " * len(line))

        return result


class FadeInEffect(Effect):
    tier = "temporal"

    @property
    def name(self) -> str:
        return "fade_in"

    def _alpha(self, t: float) -> float:
        speed = max(self.config.speed, 0.1)
        progress = (t * speed) % 2.0
        if progress > 1.0:
            progress = 2.0 - progress
        return progress

    def apply(self, lines: list[str], t: float) -> list[str]:
        return lines

    def brightness(
        self, t: float, *, row: int, col: int, char: str, lines: list[str]
    ) -> float:
        return 1.0

    def opacity(
        self, t: float, *, row: int, col: int, char: str, lines: list[str]
    ) -> float:
        return self._alpha(t)


class WipeEffect(Effect):
    tier = "temporal"

    def __init__(
        self,
        config=None,
        direction: str = "horizontal",
        loop: bool = True,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.direction = direction
        self.loop = loop

    @property
    def name(self) -> str:
        return "wipe"

    def precompute(self, banner) -> None:
        super().precompute(banner)

        rows = len(self._base_lines)
        cols = self._base_width

        self._min_row = 0
        self._max_row = max(0, rows - 1)
        self._min_col = 0
        self._max_col = max(0, cols - 1)

    def apply(self, lines: list[str], t: float) -> list[str]:
        speed = max(self.config.speed, 0.1)
        t = t * speed

        if self.loop:
            progress = t % 1.0
        else:
            progress = clamp(t, 0.0, 1.0)

        if self.direction == "vertical":
            height = self._max_row - self._min_row + 1
            cutoff = self._min_row + int(height * progress)

            return [
                line if row <= cutoff else " " * len(line)
                for row, line in enumerate(lines)
            ]

        width = self._max_col - self._min_col + 1
        cutoff_col = self._min_col + int(width * progress)

        result = []
        for line in lines:
            padded = line.ljust(self._base_width)
            result.append(padded[:cutoff_col] + " " * max(0, len(padded) - cutoff_col))

        return result


class StaggerEffect(Effect):
    tier = "temporal"

    def __init__(
        self,
        config=None,
        line_delay: float = 0.16,
        chars_per_second: float = 120.0,
        loop: bool = True,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.line_delay = line_delay
        self.chars_per_second = chars_per_second
        self.loop = loop

    @property
    def name(self) -> str:
        return "stagger"

    def apply(self, lines: list[str], t: float) -> list[str]:
        speed = max(self.config.speed, 0.1)
        t = t * speed

        if self.loop:
            # Calculate cycle time
            num_lines = len(lines)
            max_line_length = max(len(line) for line in lines) if lines else 0
            reveal_time = max_line_length / self.chars_per_second
            total_delay = (num_lines - 1) * self.line_delay
            cycle_time = total_delay + reveal_time
            t = t % cycle_time

        result: list[str] = []

        for row, line in enumerate(lines):
            local_t = max(0.0, t - row * self.line_delay)
            visible = min(len(line), int(local_t * self.chars_per_second))
            result.append(line[:visible] + " " * (len(line) - visible))

        return result
