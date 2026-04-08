"""Banner object with a composable effect and gradient pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text

from bangen.effects.base import CellStyle, RGB
from bangen.effects.utils import clamp, scale_color

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

    def apply(self, effect: "Effect") -> "Banner":
        """Append *effect* to the pipeline and return self for chaining."""
        effect.precompute(self)
        self._effects.append(effect)
        return self

    def set_gradient(self, gradient: "Gradient") -> "Banner":
        self._gradient = gradient
        return self

    def clear_effects(self) -> "Banner":
        self._effects.clear()
        return self

    def frame_lines(self, t: float) -> list[str]:
        lines = list(self.lines)
        for effect in self._effects:
            lines = effect.apply(lines, t)
        return lines

    def cell_style(
        self,
        lines: list[str],
        t: float,
        row: int,
        col: int,
        char: str,
    ) -> CellStyle:
        line_count = max(1, len(lines))
        line_length = max(1, len(lines[row]) if row < len(lines) else 0)
        position = self._base_gradient_position(
            row=row,
            col=col,
            line_length=line_length,
            line_count=line_count,
        )

        for effect in self._effects:
            position = effect.transform_gradient_position(
                position,
                t=t,
                row=row,
                col=col,
                line_length=line_length,
                line_count=line_count,
                char=char,
                lines=lines,
            )

        color = self._base_color(position)
        opacity = 1.0
        brightness = 1.0

        for effect in self._effects:
            brightness *= effect.brightness(
                t,
                row=row,
                col=col,
                char=char,
                lines=lines,
            )
            opacity *= effect.opacity(
                t,
                row=row,
                col=col,
                char=char,
                lines=lines,
            )
            color = effect.colorize(
                color,
                t=t,
                row=row,
                col=col,
                char=char,
                lines=lines,
            )

        opacity = clamp(opacity)
        color = scale_color(color, max(0.0, brightness))

        overlays = []
        for effect in self._effects:
            overlays.extend(
                effect.raster_layers(
                    t=t,
                    row=row,
                    col=col,
                    char=char,
                    lines=lines,
                    color=color,
                    opacity=opacity,
                )
            )

        return CellStyle(color=color, opacity=opacity, overlays=tuple(overlays))

    def render_frame(self, t: float) -> Text:
        lines = self.frame_lines(t)
        result = Text(no_wrap=True)

        for row, line in enumerate(lines):
            for col, char in enumerate(line):
                if char == " ":
                    result.append(" ")
                    continue
                style = self.cell_style(lines, t, row, col, char)
                if style.opacity <= 0.05:
                    result.append(" ")
                    continue
                rich_style = Style(
                    color=f"rgb({style.color[0]},{style.color[1]},{style.color[2]})",
                    dim=style.opacity < 0.6,
                )
                result.append(char, style=rich_style)
            if row < len(lines) - 1:
                result.append("\n")
        return result

    def raw_text(self) -> str:
        return "\n".join(self.lines)

    def width(self) -> int:
        return max((len(line) for line in self.lines), default=0)

    def height(self) -> int:
        return len(self.lines)

    def _base_gradient_position(
        self,
        *,
        row: int,
        col: int,
        line_length: int,
        line_count: int,
    ) -> float:
        gradient = self._gradient
        if gradient is None:
            return 0.0
        if gradient.direction == "vertical":
            return row / (line_count - 1) if line_count > 1 else 0.0
        return col / (line_length - 1) if line_length > 1 else 0.0

    def _base_color(self, position: float) -> RGB:
        if self._gradient is None:
            return (255, 255, 255)
        return self._gradient.color_at(position % 1.0)
