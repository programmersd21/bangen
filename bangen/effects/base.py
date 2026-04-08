"""Base classes for the composable effect pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bangen.rendering.banner import Banner

RGB = tuple[int, int, int]


@dataclass(slots=True)
class EffectConfig:
    """Configuration shared by all effects."""

    speed: float = 1.0
    amplitude: float = 1.0
    frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class RasterLayer:
    """Additional raster-only draw layer for glow and channel split effects."""

    dx: int = 0
    dy: int = 0
    color: RGB | None = None
    alpha: float = 1.0
    char: str | None = None


@dataclass(frozen=True, slots=True)
class CellStyle:
    """Resolved per-cell style data for terminal and raster rendering."""

    color: RGB
    opacity: float = 1.0
    overlays: tuple[RasterLayer, ...] = ()


class Effect(ABC):
    """Abstract base for all rendering effects."""

    tier: str = "general"

    def __init__(self, config: EffectConfig | None = None) -> None:
        self.config = config or EffectConfig()
        self._base_lines: tuple[str, ...] = ()
        self._base_width = 0
        self._base_height = 0

    def precompute(self, banner: "Banner") -> None:
        """Cache banner metadata for later frames."""
        self._base_lines = tuple(banner.lines)
        self._base_width = banner.width()
        self._base_height = banner.height()

    @abstractmethod
    def apply(self, lines: list[str], t: float) -> list[str]:
        """Transform *lines* at time *t* and return the modified lines."""

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
        return position

    def brightness(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        return 1.0

    def opacity(
        self,
        t: float,
        *,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> float:
        return 1.0

    def colorize(
        self,
        color: RGB,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ) -> RGB:
        return color

    def raster_layers(
        self,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
        color: RGB,
        opacity: float,
    ) -> tuple[RasterLayer, ...]:
        return ()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique lower-case identifier for this effect."""


class BrightnessModifier(ABC):
    """Compatibility mixin for older effects that only modulate brightness."""

    @abstractmethod
    def brightness(self, t: float) -> float:
        """Return a brightness multiplier in [0.0, 1.0]."""
