"""Banner object with a composable effect and gradient pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from bangen.effects.base import Effect
    from bangen.gradients.gradient import Gradient


@dataclass
class Banner:
    """Holds rendered ASCII lines and manages a composable effect pipeline."""

    text: str
    font: str
    lines: list[str]
    _effects: list["Effect"] = field(default_factory=list, repr=False)
    _gradient: "Gradient | None" = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Pipeline construction
    # ------------------------------------------------------------------

    def apply(self, effect: "Effect") -> "Banner":
        """Append *effect* to the pipeline and return self for chaining."""
        self._effects.append(effect)
        return self

    def set_gradient(self, gradient: "Gradient") -> "Banner":
        """Attach a gradient to this banner."""
        self._gradient = gradient
        return self

    def clear_effects(self) -> "Banner":
        self._effects.clear()
        return self

    # ------------------------------------------------------------------
    # Frame rendering
    # ------------------------------------------------------------------

    def render_frame(self, t: float) -> Text:
        """Apply all effects at time *t* and return a rich Text object."""
        from bangen.effects.base import BrightnessModifier

        lines = list(self.lines)
        brightness = 1.0

        for effect in self._effects:
            lines = effect.apply(lines, t)
            if isinstance(effect, BrightnessModifier):
                brightness = effect.brightness(t)

        if self._gradient is not None:
            return self._gradient.apply_multiline(lines, base_brightness=brightness)

        # Fallback: flat white with brightness applied
        b_val = min(255, int(255 * brightness))
        flat_style = Style(color=f"rgb({b_val},{b_val},{b_val})")
        result = Text()
        for i, line in enumerate(lines):
            result.append(line, style=flat_style)
            if i < len(lines) - 1:
                result.append("\n")
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def raw_text(self) -> str:
        return "\n".join(self.lines)

    def width(self) -> int:
        return max((len(ln) for ln in self.lines), default=0)

    def height(self) -> int:
        return len(self.lines)
