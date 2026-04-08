"""Effect pipeline registry and factory."""

from __future__ import annotations

from bangen.effects.base import BrightnessModifier, CellStyle, Effect, EffectConfig, RasterLayer
from bangen.effects.distortion import (
    ChromaticAberrationEffect,
    FragmentEffect,
    GlitchEffect,
    MeltEffect,
    NoiseInjectionEffect,
    ParticleDisintegrationEffect,
    WarpEffect,
)
from bangen.effects.motion import (
    BounceEffect,
    DriftEffect,
    ScrollEffect,
    ShakeEffect,
    VerticalWaveEffect,
    WaveEffect,
)
from bangen.effects.signature import (
    ElectricEffect,
    FireEffect,
    MatrixRainEffect,
    NeonSignEffect,
    VHSGlitchEffect,
    WaveInterferenceEffect,
)
from bangen.effects.temporal import FadeInEffect, StaggerEffect, TypewriterEffect, WipeEffect
from bangen.effects.visual import (
    FlickerEffect,
    GlowEffect,
    GradientShiftEffect,
    LoopPulseEffect,
    PulseEffect,
    RainbowCycleEffect,
    ScanlineEffect,
)

__all__ = [
    "Effect",
    "EffectConfig",
    "BrightnessModifier",
    "RasterLayer",
    "CellStyle",
    "WaveEffect",
    "VerticalWaveEffect",
    "BounceEffect",
    "ScrollEffect",
    "DriftEffect",
    "ShakeEffect",
    "GradientShiftEffect",
    "PulseEffect",
    "RainbowCycleEffect",
    "GlowEffect",
    "FlickerEffect",
    "ScanlineEffect",
    "TypewriterEffect",
    "FadeInEffect",
    "WipeEffect",
    "StaggerEffect",
    "LoopPulseEffect",
    "GlitchEffect",
    "ChromaticAberrationEffect",
    "NoiseInjectionEffect",
    "MeltEffect",
    "WarpEffect",
    "FragmentEffect",
    "MatrixRainEffect",
    "FireEffect",
    "ElectricEffect",
    "VHSGlitchEffect",
    "NeonSignEffect",
    "WaveInterferenceEffect",
    "ParticleDisintegrationEffect",
    "EFFECT_REGISTRY",
    "EFFECT_TIERS",
    "AVAILABLE_EFFECTS",
    "build_effect",
]

EFFECT_TIERS: dict[str, list[str]] = {
    "motion": [
        "wave",
        "vertical_wave",
        "bounce",
        "scroll",
        "drift",
        "shake",
    ],
    "visual": [
        "gradient_shift",
        "pulse",
        "rainbow_cycle",
        "glow",
        "flicker",
        "scanline",
    ],
    "temporal": [
        "typewriter",
        "fade_in",
        "wipe",
        "stagger",
        "loop_pulse",
    ],
    "distortion": [
        "glitch",
        "chromatic_aberration",
        "noise_injection",
        "melt",
        "warp",
        "fragment",
    ],
    "signature": [
        "matrix_rain",
        "fire",
        "electric",
        "vhs_glitch",
        "neon_sign",
        "wave_interference",
        "particle_disintegration",
    ],
}

EFFECT_REGISTRY: dict[str, type[Effect]] = {
    "wave": WaveEffect,
    "vertical_wave": VerticalWaveEffect,
    "bounce": BounceEffect,
    "scroll": ScrollEffect,
    "drift": DriftEffect,
    "shake": ShakeEffect,
    "gradient_shift": GradientShiftEffect,
    "pulse": PulseEffect,
    "rainbow_cycle": RainbowCycleEffect,
    "glow": GlowEffect,
    "flicker": FlickerEffect,
    "scanline": ScanlineEffect,
    "typewriter": TypewriterEffect,
    "fade_in": FadeInEffect,
    "wipe": WipeEffect,
    "stagger": StaggerEffect,
    "loop_pulse": LoopPulseEffect,
    "glitch": GlitchEffect,
    "chromatic_aberration": ChromaticAberrationEffect,
    "noise_injection": NoiseInjectionEffect,
    "melt": MeltEffect,
    "warp": WarpEffect,
    "fragment": FragmentEffect,
    "matrix_rain": MatrixRainEffect,
    "fire": FireEffect,
    "electric": ElectricEffect,
    "vhs_glitch": VHSGlitchEffect,
    "neon_sign": NeonSignEffect,
    "wave_interference": WaveInterferenceEffect,
    "particle_disintegration": ParticleDisintegrationEffect,
}

AVAILABLE_EFFECTS: list[str] = [
    name for names in EFFECT_TIERS.values() for name in names
]


def build_effect(
    name: str,
    config: EffectConfig | None = None,
    **kwargs: object,
) -> Effect:
    """Instantiate an effect by name."""
    if name not in EFFECT_REGISTRY:
        raise ValueError(f"Unknown effect {name!r}. Available: {AVAILABLE_EFFECTS}")
    effect_class = EFFECT_REGISTRY[name]
    return effect_class(config=config, **kwargs)
