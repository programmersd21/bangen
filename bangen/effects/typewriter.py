"""Typewriter effect — smooth typing line-by-line"""

from __future__ import annotations

from bangen.effects.base import Effect, EffectConfig


class TypewriterEffect(Effect):
    def __init__(
        self,
        config: EffectConfig | None = None,
        chars_per_second: float = 50.0,
        loop: bool = True,
        pause: float = 0.5,
    ) -> None:
        super().__init__(config)
        self.chars_per_second = chars_per_second
        self.loop = loop
        self.pause = pause

    @property
    def name(self) -> str:
        return "typewriter"

    def apply(self, lines: list[str], t: float) -> list[str]:
        text = "\n".join(lines)
        total_chars = len(text)

        if total_chars == 0:
            return lines

        typing_time = total_chars / (self.chars_per_second * self.config.speed)
        cycle_time = typing_time + self.pause

        if self.loop:
            t = t % cycle_time
        else:
            t = min(t, typing_time)

        if t >= typing_time:
            revealed = total_chars
        else:
            reveal_f = t * self.chars_per_second * self.config.speed
            revealed = int(reveal_f + 0.5)

        visible = text[:revealed]
        split = visible.split("\n")

        result: list[str] = []

        for i, line in enumerate(lines):
            if i < len(split):
                current = split[i]
                padded = current + " " * (len(line) - len(current))
                result.append(padded)
            else:
                result.append(" " * len(line))

        return result