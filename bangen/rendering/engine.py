"""Core ASCII rendering engine backed by pyfiglet."""

from __future__ import annotations

from pathlib import Path

import pyfiglet

from bangen.rendering.banner import Banner

DEFAULT_FONT = "ansi_shadow"

PRESET_FONTS: list[str] = [
    "ansi_shadow",
    "slant",
    "standard",
    "block",
    "big",
    "banner3-D",
    "speed",
    "doom",
    "starwars",
    "small",
    "smslant",
    "3-d",
    "roman",
    "larry3d",
    "epic",
]


class RenderEngine:
    """Renders text into ASCII art banners using FIGlet fonts."""

    def __init__(self, font_dirs: list[Path] | None = None) -> None:
        self._font_dirs: list[Path] = font_dirs or []
        self._available: set[str] | None = None

    # ------------------------------------------------------------------
    # Font discovery
    # ------------------------------------------------------------------

    def _load_fonts(self) -> None:
        try:
            self._available = set(pyfiglet.FigletFont.getFonts())
        except Exception:
            self._available = set(PRESET_FONTS)

        for d in self._font_dirs:
            if d.is_dir():
                for flf in d.glob("*.flf"):
                    self._available.add(flf.stem)

    def available_fonts(self) -> set[str]:
        if self._available is None:
            self._load_fonts()
        assert self._available is not None
        return self._available

    def add_font_dir(self, directory: Path) -> None:
        self._font_dirs.append(directory)
        self._available = None  # invalidate cache

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _make_figlet(self, font: str) -> pyfiglet.Figlet:
        """Return a Figlet instance, searching custom dirs first."""
        for d in self._font_dirs:
            flf = d / f"{font}.flf"
            if flf.exists():
                try:
                    return pyfiglet.Figlet(font=str(flf))
                except Exception:
                    pass
        try:
            return pyfiglet.Figlet(font=font)
        except pyfiglet.FontNotFound:
            return pyfiglet.Figlet(font=DEFAULT_FONT)

    def render(self, text: str, font: str = DEFAULT_FONT) -> Banner:
        """Render *text* with *font* and return a :class:`Banner`."""
        if not text:
            text = " "

        known = self.available_fonts()
        actual_font = font if font in known else DEFAULT_FONT

        figlet = self._make_figlet(actual_font)
        rendered = figlet.renderText(text)
        lines = rendered.rstrip("\n").splitlines()

        return Banner(text=text, font=actual_font, lines=lines)
