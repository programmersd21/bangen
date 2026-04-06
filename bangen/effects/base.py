"""Base classes for the composable effect pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EffectConfig:
    """Configuration shared by all effects."""

    speed: float = 1.0
    amplitude: float = 1.0
    frequency: float = 1.0


class Effect(ABC):
    """Abstract base for all rendering effects."""

    def __init__(self, config: EffectConfig | None = None) -> None:
        self.config = config or EffectConfig()

    @abstractmethod
    def apply(self, lines: list[str], t: float) -> list[str]:
        """Transform *lines* at time *t* and return the modified lines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique lower-case identifier for this effect."""


class BrightnessModifier(ABC):
    """
    Mixin for effects that want to modulate global brightness instead of
    (or in addition to) modifying character content.
    """

    @abstractmethod
    def brightness(self, t: float) -> float:
        """Return a brightness multiplier in [0.0, 1.0]."""
