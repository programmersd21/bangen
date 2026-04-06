"""Rule-based prompt-to-banner style suggester with optional LLM hook."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StyleSuggestion:
    font: str
    gradient: str
    gradient_direction: str = "horizontal"
    effects: list[str] = field(default_factory=list)
    effect_config: dict[str, Any] = field(default_factory=dict)


_FONT_RULES: list[tuple[set[str], str]] = [
    (
        {"cyberpunk", "hacker", "tech", "digital", "matrix", "code", "terminal", "cli"},
        "slant",
    ),
    ({"retro", "arcade", "pixel", "8bit", "80s", "vintage", "classic", "old"}, "doom"),
    ({"neon", "glow", "vaporwave", "synthwave", "rave", "plasma"}, "ansi_shadow"),
    ({"space", "scifi", "star", "galaxy", "cosmic", "alien", "universe"}, "starwars"),
    ({"bold", "heavy", "strong", "impact", "chunky", "thick"}, "block"),
    ({"fast", "speed", "rush", "turbo", "race", "zoom"}, "speed"),
    ({"small", "minimal", "clean", "simple", "tiny", "micro"}, "small"),
    ({"gothic", "dark", "medieval", "shadow", "doom", "death"}, "larry3d"),
    ({"epic", "hero", "legend", "giant", "massive", "huge"}, "epic"),
    ({"roman", "ancient", "classic", "formal", "elegant"}, "roman"),
]

_GRADIENT_RULES: list[tuple[set[str], str]] = [
    ({"neon", "cyberpunk", "hacker", "electric", "plasma"}, "#ff00ff:#00ffff"),
    (
        {"fire", "hot", "burn", "flame", "inferno", "lava", "warm"},
        "#ff0000:#ff6600:#ffff00",
    ),
    (
        {"ocean", "water", "sea", "wave", "aqua", "blue", "navy"},
        "#000080:#0080ff:#00ffff",
    ),
    ({"matrix", "hacker", "code", "terminal", "green", "console"}, "#003300:#00ff00"),
    ({"sunset", "evening", "dusk", "orange", "twilight"}, "#ff6600:#ff00ff:#6600ff"),
    ({"vaporwave", "retro", "80s", "synthwave", "aesthetic"}, "#ff00aa:#aa00ff"),
    (
        {"gold", "luxury", "royal", "premium", "rich", "wealth"},
        "#ffaa00:#ffff00:#ffaa00",
    ),
    ({"space", "galaxy", "cosmic", "dark", "void", "night"}, "#0000ff:#6600ff:#ff00ff"),
    (
        {"rainbow", "colorful", "pride", "spectrum", "vibrant"},
        "#ff0000:#ff8800:#ffff00:#00ff00:#0000ff:#8800ff",
    ),
    (
        {"electric", "lightning", "thunder", "power", "voltage"},
        "#0088ff:#00ffff:#ffffff",
    ),
    ({"blood", "horror", "scary", "dark", "red", "danger"}, "#330000:#ff0000"),
    ({"nature", "forest", "leaf", "eco", "green", "plant"}, "#003300:#00aa00:#00ff88"),
    ({"ice", "snow", "frost", "cold", "winter", "arctic"}, "#88ccff:#ffffff:#88ccff"),
    (
        {"candy", "sweet", "pink", "cute", "pastel", "bubblegum"},
        "#ff88cc:#ffccee:#ff44aa",
    ),
]

_EFFECT_RULES: list[tuple[set[str], list[str], dict[str, Any]]] = [
    (
        {"wave", "ocean", "flow", "ripple", "undulate"},
        ["wave"],
        {"wave": {"speed": 1.5, "amplitude": 2.0}},
    ),
    (
        {"glitch", "corrupt", "broken", "error", "hack", "distort"},
        ["glitch"],
        {"glitch": {"intensity": 0.1}},
    ),
    (
        {"pulse", "heartbeat", "breathe", "live", "throb", "beat"},
        ["pulse"],
        {"pulse": {"speed": 1.5}},
    ),
    (
        {"type", "typewriter", "write", "print", "reveal", "appear"},
        ["typewriter"],
        {"typewriter": {"chars_per_second": 60.0}},
    ),
    (
        {"scroll", "ticker", "news", "loop", "slide", "marquee"},
        ["scroll"],
        {"scroll": {"speed": 1.0}},
    ),
    (
        {"neon", "glow", "electric", "energy"},
        ["pulse", "wave"],
        {"pulse": {"speed": 2.0}, "wave": {"speed": 1.0, "amplitude": 1.5}},
    ),
    (
        {"cyberpunk", "glitchy", "hacker", "corrupt"},
        ["glitch", "pulse"],
        {"glitch": {"intensity": 0.08}, "pulse": {"speed": 1.0}},
    ),
    (
        {"vaporwave", "dreamy", "chill", "slow"},
        ["scroll", "pulse"],
        {"scroll": {"speed": 0.5}, "pulse": {"speed": 0.6}},
    ),
    (
        {"storm", "lightning", "chaos", "wild"},
        ["glitch", "wave"],
        {"glitch": {"intensity": 0.15}, "wave": {"speed": 3.0, "amplitude": 2.0}},
    ),
]

_DEFAULT_FONT = "ansi_shadow"
_DEFAULT_GRADIENT = "#00ffff:#ff00ff"


def _tokenize(prompt: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z]+", prompt.lower()))


def suggest_from_prompt(prompt: str) -> StyleSuggestion:
    tokens = _tokenize(prompt)

    font = _DEFAULT_FONT
    for keywords, f in _FONT_RULES:
        if tokens & keywords:
            font = f
            break

    gradient = _DEFAULT_GRADIENT
    for keywords, g in _GRADIENT_RULES:
        if tokens & keywords:
            gradient = g
            break

    effects: list[str] = []
    effect_config: dict[str, Any] = {}
    for keywords, efx, cfg in _EFFECT_RULES:
        if tokens & keywords:
            effects = efx
            effect_config = cfg
            break

    return StyleSuggestion(
        font=font,
        gradient=gradient,
        gradient_direction="horizontal",
        effects=effects,
        effect_config=effect_config,
    )


def suggest_to_preset(name: str, prompt: str) -> "Preset":  # noqa: F821
    from bangen.presets.manager import Preset

    s = suggest_from_prompt(prompt)
    return Preset(
        name=name,
        font=s.font,
        gradient=s.gradient,
        gradient_direction=s.gradient_direction,
        effects=s.effects,
        effect_config=s.effect_config,
    )
