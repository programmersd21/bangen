"""Glitch effect — stochastic character substitution."""

from __future__ import annotations

import random

from bangen.effects.base import Effect, EffectConfig

_GLITCH_CHARS: str = "!@#$%^&*<>[]{}|\\/?~`±§"


class GlitchEffect(Effect):
    """Randomly replaces non-space characters with glitch symbols."""

    def __init__(
        self,
        config: EffectConfig | None = None,
        intensity: float = 0.05,
    ) -> None:
        super().__init__(config)
        self.intensity = intensity

    @property
    def name(self) -> str:
        return "glitch"

    def apply(self, lines: list[str], t: float) -> list[str]:
        # Seed from quantised time so the glitch "frame" is stable within a tick
        rng = random.Random(int(t * 24))
        effective_intensity = min(1.0, self.intensity * self.config.amplitude)

        result: list[str] = []
        for line in lines:
            chars: list[str] = []
            for ch in line:
                if ch != " " and rng.random() < effective_intensity:
                    chars.append(rng.choice(_GLITCH_CHARS))
                else:
                    chars.append(ch)
            result.append("".join(chars))
        return result
