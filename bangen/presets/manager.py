"""Preset management — built-in library + user-defined JSON storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PRESETS_DIR: Path = Path.home() / ".bangen" / "presets"


@dataclass
class Preset:
    """Complete styling configuration for a banner."""

    name: str
    font: str
    gradient: str
    gradient_direction: str = "horizontal"
    effects: list[str] = field(default_factory=list)
    effect_config: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "font": self.font,
            "gradient": self.gradient,
            "gradient_direction": self.gradient_direction,
            "effects": self.effects,
            "effect_config": self.effect_config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Preset":
        return cls(
            name=data["name"],
            font=data.get("font", "ansi_shadow"),
            gradient=data.get("gradient", "#00ffff:#ff00ff"),
            gradient_direction=data.get("gradient_direction", "horizontal"),
            effects=data.get("effects", []),
            effect_config=data.get("effect_config", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ---------------------------------------------------------------------------
# Built-in preset library
# ---------------------------------------------------------------------------

BUILTIN_PRESETS: dict[str, Preset] = {
    "neon_wave": Preset(
        name="neon_wave",
        font="ansi_shadow",
        gradient="#ff00ff:#00ffff:#ff00ff",
        effects=["wave", "pulse"],
        effect_config={
            "wave": {"speed": 2.0, "amplitude": 2.0, "frequency": 0.5},
            "pulse": {"speed": 1.5},
        },
    ),
    "cyberpunk": Preset(
        name="cyberpunk",
        font="slant",
        gradient="#ff0080:#ffff00:#00ff80",
        effects=["glitch"],
        effect_config={"glitch": {"intensity": 0.08}},
    ),
    "matrix": Preset(
        name="matrix",
        font="banner3-D",
        gradient="#003300:#00ff00",
        gradient_direction="vertical",
        effects=["typewriter"],
        effect_config={"typewriter": {"chars_per_second": 80.0, "speed": 1.0}},
    ),
    "retro": Preset(
        name="retro",
        font="doom",
        gradient="#ff6600:#ffcc00",
        effects=[],
        effect_config={},
    ),
    "ocean": Preset(
        name="ocean",
        font="speed",
        gradient="#000080:#0080ff:#00ffff",
        gradient_direction="vertical",
        effects=["wave"],
        effect_config={"wave": {"speed": 1.0, "amplitude": 1.5, "frequency": 0.8}},
    ),
    "vaporwave": Preset(
        name="vaporwave",
        font="small",
        gradient="#ff00aa:#aa00ff:#0044ff",
        effects=["scroll", "pulse"],
        effect_config={
            "scroll": {"speed": 0.8},
            "pulse": {"speed": 0.7, "min_brightness": 0.4},
        },
    ),
    "electric": Preset(
        name="electric",
        font="ansi_shadow",
        gradient="#0088ff:#00ffff:#ffffff:#00ffff:#0088ff",
        effects=["glitch", "pulse"],
        effect_config={
            "glitch": {"intensity": 0.04},
            "pulse": {"speed": 3.0, "min_brightness": 0.6},
        },
    ),
    "fire": Preset(
        name="fire",
        font="block",
        gradient="#ff0000:#ff6600:#ffff00",
        gradient_direction="vertical",
        effects=["wave", "glitch"],
        effect_config={
            "wave": {"speed": 3.0, "amplitude": 1.0, "frequency": 1.5},
            "glitch": {"intensity": 0.02},
        },
    ),
}


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class PresetManager:
    """Load, save, list, and delete user-defined and built-in presets."""

    def __init__(self, presets_dir: Path = DEFAULT_PRESETS_DIR) -> None:
        self._dir = presets_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._user: dict[str, Preset] = {}
        self._scan()

    def _scan(self) -> None:
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                preset = Preset.from_dict(data)
                self._user[preset.name] = preset
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_presets(self) -> dict[str, Preset]:
        """Return merged dict of built-in + user presets (user wins on collision)."""
        merged = dict(BUILTIN_PRESETS)
        merged.update(self._user)
        return merged

    def get(self, name: str) -> Preset | None:
        """Return the preset with *name*, checking user presets first."""
        return self._user.get(name) or BUILTIN_PRESETS.get(name)

    def save(self, preset: Preset) -> None:
        path = self._dir / f"{preset.name}.json"
        path.write_text(preset.to_json(), encoding="utf-8")
        self._user[preset.name] = preset

    def delete(self, name: str) -> bool:
        path = self._dir / f"{name}.json"
        if path.exists():
            path.unlink()
            self._user.pop(name, None)
            return True
        return False

    def export_all(self, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, preset in self.list_presets().items():
            (target_dir / f"{name}.json").write_text(preset.to_json(), encoding="utf-8")
