"""Pulse effect — brightness oscillation via the BrightnessModifier protocol."""

from __future__ import annotations

import math

from bangen.effects.base import BrightnessModifier, Effect, EffectConfig


class PulseEffect(Effect, BrightnessModifier):
    """Oscillates global rendering brightness using a sine wave."""

    def __init__(
        self,
        config: EffectConfig | None = None,
        min_brightness: float = 0.25,
        max_brightness: float = 1.0,
    ) -> None:
        super().__init__(config)
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness

    @property
    def name(self) -> str:
        return "pulse"

    def apply(self, lines: list[str], t: float) -> list[str]:
        # Content is not modified; brightness is driven via brightness()
        return lines

    def brightness(self, t: float) -> float:
        phase = math.sin(t * self.config.speed * math.pi)
        # Normalise sin from [-1, 1] to [min_brightness, max_brightness]
        normalised = (phase + 1.0) / 2.0
        return self.min_brightness + normalised * (
            self.max_brightness - self.min_brightness
        )
