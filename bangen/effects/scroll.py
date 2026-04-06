"""Scroll effect — continuous horizontal banner movement."""

from __future__ import annotations

from bangen.effects.base import Effect


class ScrollEffect(Effect):
    """Scrolls all lines horizontally in a repeating loop."""

    @property
    def name(self) -> str:
        return "scroll"

    def apply(self, lines: list[str], t: float) -> list[str]:
        if not lines:
            return lines

        max_width = max(len(line) for line in lines)
        if max_width == 0:
            return lines

        offset = int(t * self.config.speed * 10) % max_width

        result: list[str] = []
        for line in lines:
            padded = line.ljust(max_width)
            scrolled = padded[offset:] + padded[:offset]
            result.append(scrolled)
        return result
