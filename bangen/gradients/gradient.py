"""Per-character RGB gradient engine with multi-stop support."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rich.style import Style
from rich.text import Text

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Parse a hex colour string (with or without leading #) into (R, G, B)."""
    hx = hex_color.strip().lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    if len(hx) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", hx):
        raise ValueError(f"Invalid hex colour: {hex_color!r}")
    return int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _interpolate(
    stops: list[tuple[float, tuple[int, int, int]]],
    t: float,
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            local = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return (
                round(_lerp(c0[0], c1[0], local)),
                round(_lerp(c0[1], c1[1], local)),
                round(_lerp(c0[2], c1[2], local)),
            )
    return stops[-1][1]


# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColorStop:
    """A single colour stop within a gradient."""

    position: float  # normalised 0.0 – 1.0
    color: str  # hex string e.g. "#ff00ff"


class Gradient:
    """
    Multi-stop true-colour gradient that can be applied per-character.

    Directions
    ----------
    * ``"horizontal"`` — colour varies left-to-right within each line.
    * ``"vertical"``   — colour varies top-to-bottom across lines.
    """

    def __init__(
        self,
        stops: list[ColorStop],
        direction: str = "horizontal",
    ) -> None:
        if len(stops) < 2:
            raise ValueError("A gradient requires at least two colour stops.")
        if direction not in ("horizontal", "vertical"):
            raise ValueError(
                f"Invalid direction {direction!r}. Use 'horizontal' or 'vertical'."
            )

        self.stops = sorted(stops, key=lambda s: s.position)
        self.direction = direction
        self._parsed: list[tuple[float, tuple[int, int, int]]] = [
            (s.position, _hex_to_rgb(s.color)) for s in self.stops
        ]

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_hex_list(
        cls,
        colors: list[str],
        direction: str = "horizontal",
    ) -> "Gradient":
        """Build a gradient from an evenly-spaced list of hex strings."""
        n = len(colors)
        if n < 2:
            raise ValueError("Need at least two colours.")
        stops = [ColorStop(position=i / (n - 1), color=c) for i, c in enumerate(colors)]
        return cls(stops=stops, direction=direction)

    @classmethod
    def from_string(
        cls,
        gradient_str: str,
        direction: str = "horizontal",
    ) -> "Gradient":
        """
        Parse a colon-separated hex string like ``"#ff00ff:#00ff00:#0000ff"``.
        Stops may optionally carry a position prefix: ``"0.0:#ff0000,1.0:#0000ff"``.
        """
        if "," in gradient_str and ":" not in gradient_str.split(",")[0]:
            # position:color,position:color format
            stops: list[ColorStop] = []
            for part in gradient_str.split(","):
                pos_str, color = part.split(":")
                stops.append(ColorStop(position=float(pos_str), color=color))
            return cls(stops=stops, direction=direction)
        else:
            colors = gradient_str.split(":")
            return cls.from_hex_list(colors, direction=direction)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def color_at(self, t: float) -> tuple[int, int, int]:
        """Return the (R, G, B) tuple at normalised position *t*."""
        return _interpolate(self._parsed, t)

    def apply(self, text: str, base_brightness: float = 1.0) -> Text:
        """Apply gradient horizontally to a single line, returning rich.Text."""
        rich_text = Text()
        chars = list(text)
        n = len(chars)
        for i, ch in enumerate(chars):
            t = i / (n - 1) if n > 1 else 0.0
            r, g, b = self.color_at(t)
            r = min(255, round(r * base_brightness))
            g = min(255, round(g * base_brightness))
            b = min(255, round(b * base_brightness))
            rich_text.append(ch, style=Style(color=f"rgb({r},{g},{b})"))
        return rich_text

    def apply_multiline(
        self,
        lines: list[str],
        base_brightness: float = 1.0,
    ) -> Text:
        """Apply gradient to multiple lines, returning a single rich.Text."""
        rich_text = Text(no_wrap=True)
        n_lines = len(lines)

        for line_idx, line in enumerate(lines):
            chars = list(line)
            n_chars = len(chars)

            for col_idx, ch in enumerate(chars):
                if self.direction == "horizontal":
                    t = col_idx / (n_chars - 1) if n_chars > 1 else 0.0
                else:
                    t = line_idx / (n_lines - 1) if n_lines > 1 else 0.0

                r, g, b = self.color_at(t)
                r = min(255, round(r * base_brightness))
                g = min(255, round(g * base_brightness))
                b = min(255, round(b * base_brightness))
                rich_text.append(ch, style=Style(color=f"rgb({r},{g},{b})"))

            if line_idx < n_lines - 1:
                rich_text.append("\n")

        return rich_text

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        colors = ":".join(s.color for s in self.stops)
        return f"Gradient({colors!r}, direction={self.direction!r})"
