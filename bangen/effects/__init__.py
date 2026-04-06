"""Effect pipeline — registry and factory."""

from __future__ import annotations

from bangen.effects.base import BrightnessModifier, Effect, EffectConfig
from bangen.effects.glitch import GlitchEffect
from bangen.effects.pulse import PulseEffect
from bangen.effects.scroll import ScrollEffect
from bangen.effects.typewriter import TypewriterEffect
from bangen.effects.wave import WaveEffect

__all__ = [
    "Effect",
    "EffectConfig",
    "BrightnessModifier",
    "WaveEffect",
    "GlitchEffect",
    "PulseEffect",
    "TypewriterEffect",
    "ScrollEffect",
    "EFFECT_REGISTRY",
    "build_effect",
]

EFFECT_REGISTRY: dict[str, type[Effect]] = {
    "wave": WaveEffect,
    "glitch": GlitchEffect,
    "pulse": PulseEffect,
    "typewriter": TypewriterEffect,
    "scroll": ScrollEffect,
}

AVAILABLE_EFFECTS: list[str] = list(EFFECT_REGISTRY.keys())


def build_effect(
    name: str,
    config: EffectConfig | None = None,
    **kwargs: object,
) -> Effect:
    """
    Instantiate an effect by name.

    Extra *kwargs* are forwarded to constructors that accept them
    (e.g. ``chars_per_second`` for TypewriterEffect, ``intensity`` for
    GlitchEffect).
    """
    if name not in EFFECT_REGISTRY:
        raise ValueError(f"Unknown effect {name!r}. Available: {AVAILABLE_EFFECTS}")
    cls = EFFECT_REGISTRY[name]
    if name == "typewriter":
        return TypewriterEffect(
            config=config,
            chars_per_second=float(kwargs.get("chars_per_second", 50.0)),
        )
    if name == "glitch":
        return GlitchEffect(
            config=config,
            intensity=float(kwargs.get("intensity", 0.05)),
        )
    if name == "pulse":
        return PulseEffect(
            config=config,
            min_brightness=float(kwargs.get("min_brightness", 0.25)),
            max_brightness=float(kwargs.get("max_brightness", 1.0)),
        )
    return cls(config=config)
