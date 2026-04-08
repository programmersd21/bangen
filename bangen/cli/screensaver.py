"""Terminal screensaver mode for full-screen animated banner playback."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from rich.align import Align
from rich.console import Console, ConsoleRenderable
from rich.live import Live

from bangen.effects import EffectConfig, build_effect
from bangen.gradients.gradient import Gradient
from bangen.rendering.banner import Banner
from bangen.rendering.engine import DEFAULT_FONT, RenderEngine, PRESET_FONTS

_SCREENSAFE_TIERS: dict[str, tuple[str, ...]] = {
    "motion": ("wave", "vertical_wave", "bounce", "drift", "shake"),
    "visual": (
        "gradient_shift",
        "pulse",
        "rainbow_cycle",
        "glow",
        "flicker",
        "scanline",
        "loop_pulse",
    ),
    "temporal": ("fade_in", "wipe", "stagger", "typewriter"),
    "distortion": (
        "glitch",
        "chromatic_aberration",
        "noise_injection",
        "melt",
        "warp",
        "fragment",
    ),
    "signature": (
        "matrix_rain",
        "fire",
        "electric",
        "vhs_glitch",
        "neon_sign",
        "wave_interference",
        "particle_disintegration",
    ),
}

_RANDOM_GRADIENTS: tuple[str, ...] = (
    "#7c3aed:#06b6d4",
    "#00f5d4:#00bbf9:#9b5de5",
    "#ff6b6b:#ffd166:#06d6a0",
    "#f72585:#7209b7:#4cc9f0",
    "#00ff87:#60efff",
    "#f97316:#facc15:#f8fafc",
)


@dataclass(slots=True)
class ScreensaverScene:
    banner: Banner
    started_at: float
    duration: float
    font: str
    gradient: str
    gradient_direction: str
    effects: tuple[str, ...]


def run_screensaver(
    console: Console,
    engine: RenderEngine,
    *,
    text: str,
    preferred_font: str | None,
    preferred_gradient: str | None,
    preferred_gradient_direction: str | None,
    seed: int | None = None,
    duration: float | None = None,
) -> None:
    """Run the full-screen terminal screensaver until interrupted or timed out."""

    rng = random.Random(seed)
    scene: ScreensaverScene | None = None
    terminal_size = (0, 0)
    started = time.monotonic()
    stop_at = (started + duration) if duration and duration > 0 else None

    try:
        with Live(
            console=console,
            refresh_per_second=20,
            screen=True,
            auto_refresh=False,
        ) as live:
            while True:
                now = time.monotonic()
                if stop_at is not None and now >= stop_at:
                    break

                size = (console.size.width, console.size.height)
                if (
                    scene is None
                    or size != terminal_size
                    or (now - scene.started_at) >= scene.duration
                ):
                    terminal_size = size
                    scene = _build_scene(
                        engine,
                        text=text,
                        width=size[0],
                        height=size[1],
                        preferred_font=preferred_font,
                        preferred_gradient=preferred_gradient,
                        preferred_gradient_direction=preferred_gradient_direction,
                        rng=rng,
                        now=now,
                    )

                assert scene is not None
                frame = scene.banner.render_frame(now - scene.started_at)
                live.update(_centered(frame, width=terminal_size[0], height=terminal_size[1]))
                live.refresh()
                time.sleep(0.05)
    except KeyboardInterrupt:
        return


def _build_scene(
    engine: RenderEngine,
    *,
    text: str,
    width: int,
    height: int,
    preferred_font: str | None,
    preferred_gradient: str | None,
    preferred_gradient_direction: str | None,
    rng: random.Random,
    now: float,
) -> ScreensaverScene:
    selected_effects = _pick_effects(rng)
    banner = _fit_banner(
        engine,
        text=text,
        width=width,
        height=height,
        preferred_font=preferred_font,
        active_effects=selected_effects,
        rng=rng,
    )
    gradient_str = preferred_gradient or rng.choice(_RANDOM_GRADIENTS)
    gradient_direction = preferred_gradient_direction or rng.choice(
        ("horizontal", "vertical")
    )
    try:
        banner.set_gradient(
            Gradient.from_string(gradient_str, direction=gradient_direction)
        )
    except Exception:
        banner.set_gradient(
            Gradient.from_string("#00ffff:#ff00ff", direction="horizontal")
        )
        gradient_str = "#00ffff:#ff00ff"
        gradient_direction = "horizontal"

    for effect_name in selected_effects:
        cfg, kwargs = _effect_settings(effect_name, rng)
        try:
            banner.apply(build_effect(effect_name, config=cfg, **kwargs))
        except Exception:
            continue

    duration = rng.uniform(5.5, 10.0)
    if any(name in _SCREENSAFE_TIERS["temporal"] for name in selected_effects):
        duration = rng.uniform(4.0, 7.0)

    return ScreensaverScene(
        banner=banner,
        started_at=now,
        duration=duration,
        font=banner.font,
        gradient=gradient_str,
        gradient_direction=gradient_direction,
        effects=tuple(selected_effects),
    )


def _fit_banner(
    engine: RenderEngine,
    *,
    text: str,
    width: int,
    height: int,
    preferred_font: str | None,
    active_effects: list[str] | None = None,
    rng: random.Random | None = None,
) -> Banner:
    effect_margin_x = 6
    effect_margin_y = 3
    active = set(active_effects or ())
    if active & {"wave", "wave_interference", "fragment", "vhs_glitch", "glitch"}:
        effect_margin_x += 6
    if active & {"vertical_wave", "bounce", "drift", "melt", "particle_disintegration"}:
        effect_margin_y += 3

    max_width = max(8, width - effect_margin_x)
    max_height = max(4, height - effect_margin_y)

    candidates: list[str] = []
    if preferred_font:
        candidates.append(preferred_font)
    for font in PRESET_FONTS:
        if font not in candidates:
            candidates.append(font)

    best_fits: list[tuple[float, Banner]] = []
    best_overflow: tuple[float, Banner] | None = None

    for font in candidates:
        banner = engine.render(text, font)
        banner_width = max(1, banner.width())
        banner_height = max(1, banner.height())
        fits = banner_width <= max_width and banner_height <= max_height

        if fits:
            width_ratio = banner_width / max_width
            height_ratio = banner_height / max_height
            score = (width_ratio * height_ratio * 2.5) + min(width_ratio, height_ratio)
            best_fits.append((score, banner))
            continue

        overflow = max(banner_width / max_width, banner_height / max_height)
        if best_overflow is None or overflow < best_overflow[0]:
            best_overflow = (overflow, banner)

    if best_fits:
        best_fits.sort(key=lambda item: item[0], reverse=True)
        pool_size = min(4, len(best_fits))
        pool = best_fits[:pool_size]
        chooser = rng or random
        return chooser.choice(pool)[1]
    if best_overflow is not None:
        return best_overflow[1]
    return engine.render(text, preferred_font or DEFAULT_FONT)


def _pick_effects(rng: random.Random) -> list[str]:
    chosen: list[str] = []

    anchor_tiers = ["motion", "signature", "distortion"]
    anchor_tier = rng.choice(anchor_tiers)
    chosen.append(rng.choice(_SCREENSAFE_TIERS[anchor_tier]))

    if rng.random() < 0.78:
        chosen.append(rng.choice(_SCREENSAFE_TIERS["visual"]))

    if rng.random() < 0.38:
        chosen.append(rng.choice(_SCREENSAFE_TIERS["temporal"]))

    if rng.random() < 0.42:
        extra_tiers = [
            tier
            for tier in ("motion", "distortion", "signature")
            if tier != anchor_tier
        ]
        extra_tier = rng.choice(extra_tiers)
        candidate = rng.choice(_SCREENSAFE_TIERS[extra_tier])
        if candidate not in chosen:
            chosen.append(candidate)

    if "particle_disintegration" in chosen and "wipe" in chosen:
        chosen.remove("wipe")

    if "typewriter" in chosen and "stagger" in chosen:
        chosen.remove("stagger")

    return chosen


def _effect_settings(
    effect_name: str,
    rng: random.Random,
) -> tuple[EffectConfig, dict[str, object]]:
    speed = rng.uniform(0.65, 1.9)
    amplitude = rng.uniform(0.55, 2.4)
    frequency = rng.uniform(0.55, 1.75)
    kwargs: dict[str, object] = {}

    if effect_name in {"wave", "vertical_wave", "wave_interference"}:
        amplitude = rng.uniform(1.0, 3.0)
        frequency = rng.uniform(0.5, 1.35)
    elif effect_name in {"bounce", "drift", "shake"}:
        amplitude = rng.uniform(0.8, 2.2)
    elif effect_name == "scroll":
        speed = rng.uniform(0.8, 1.35)
        amplitude = 1.0
    elif effect_name == "pulse":
        speed = rng.uniform(0.55, 1.35)
        amplitude = 1.0
        kwargs["min_brightness"] = rng.uniform(0.45, 0.65)
    elif effect_name == "loop_pulse":
        speed = rng.uniform(0.55, 1.35)
        amplitude = 1.0
    elif effect_name == "flicker":
        amplitude = rng.uniform(0.4, 1.0)
        speed = rng.uniform(0.7, 1.15)
    elif effect_name == "scanline":
        speed = rng.uniform(0.75, 1.4)
        amplitude = 1.0
    elif effect_name == "glitch":
        amplitude = rng.uniform(0.6, 1.2)
        kwargs["intensity"] = rng.uniform(0.025, 0.08)
    elif effect_name == "fragment":
        amplitude = rng.uniform(0.5, 1.0)
        kwargs["chunk_width"] = rng.randint(4, 8)
    elif effect_name == "wipe":
        speed = rng.uniform(0.45, 0.9)
        amplitude = 1.0
        kwargs["direction"] = rng.choice(("horizontal", "vertical"))
        kwargs["loop"] = True
    elif effect_name == "typewriter":
        speed = rng.uniform(0.85, 1.35)
        amplitude = 1.0
        kwargs["chars_per_second"] = rng.uniform(38.0, 90.0)
        kwargs["pause"] = rng.uniform(0.25, 0.85)
        kwargs["loop"] = True
    elif effect_name == "stagger":
        speed = rng.uniform(0.9, 1.35)
        amplitude = 1.0
        kwargs["line_delay"] = rng.uniform(0.08, 0.18)
        kwargs["chars_per_second"] = rng.uniform(70.0, 150.0)
    elif effect_name == "fade_in":
        speed = rng.uniform(0.5, 1.1)
        amplitude = 1.0
    elif effect_name == "matrix_rain":
        speed = rng.uniform(0.7, 1.3)
        amplitude = rng.uniform(0.8, 2.0)
    elif effect_name in {"fire", "electric", "neon_sign", "vhs_glitch"}:
        amplitude = rng.uniform(0.7, 1.7)
        speed = rng.uniform(0.75, 1.35)
    elif effect_name == "particle_disintegration":
        amplitude = rng.uniform(0.7, 1.5)
        speed = rng.uniform(0.8, 1.2)

    return EffectConfig(speed=speed, amplitude=amplitude, frequency=frequency), kwargs


def _centered(content: ConsoleRenderable, *, width: int, height: int) -> ConsoleRenderable:
    return Align.center(content, vertical="middle", width=width, height=height)
