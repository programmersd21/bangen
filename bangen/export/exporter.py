"""Export engine dispatch and validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bangen.export.gif import export_gif, normalize_gif_settings
from bangen.export.png import export_png
from bangen.export.txt import export_txt

if TYPE_CHECKING:
    from bangen.gradients.gradient import Gradient
    from bangen.rendering.banner import Banner


class Exporter:
    """Converts a Banner into various output formats."""

    def export_txt(self, banner: "Banner", path: str | Path) -> None:
        target = self._prepare_path(path)
        self._validate_banner(banner)
        target.parent.mkdir(parents=True, exist_ok=True)
        export_txt(target, banner.raw_text())

    def export_gif(
        self,
        banner: "Banner",
        path: str | Path,
        duration: float,
        fps: float,
    ) -> None:
        target = self._prepare_path(path)
        self._validate_banner(banner)
        normalize_gif_settings(duration, fps)
        target.parent.mkdir(parents=True, exist_ok=True)
        export_gif(target, banner, duration, fps)

    def export_html(
        self, banner: "Banner", path: str | Path, gradient: "Gradient | None" = None
    ) -> None:
        target = self._prepare_path(path)
        self._validate_banner(banner)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = banner.frame_lines(0.0)
        lines_html: list[str] = []
        for li, line in enumerate(lines):
            spans: list[str] = []
            for ci, ch in enumerate(line):
                style = banner.cell_style(lines, 0.0, li, ci, ch)
                color = self._rgb_to_hex(style.color if ch != " " else self._rgb(gradient, ci, len(line), li, len(lines)))
                esc = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                spans.append(
                    f'<span style="color:{color}">{esc if esc.strip() else "&nbsp;"}</span>'
                )
            lines_html.append("".join(spans))
        body = "<br>\n".join(lines_html)
        html = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n<title>Bangen Export</title>\n'
            '<style>body{background:#0a0a0a;font-family:"Courier New",Courier,monospace;'
            "font-size:14px;line-height:1.3;padding:2rem;white-space:pre;}</style>\n"
            f"</head>\n<body>\n{body}\n</body>\n</html>"
        )
        target.write_text(html, encoding="utf-8")

    def export_png(
        self, banner: "Banner", path: str | Path, gradient: "Gradient | None" = None
    ) -> None:
        target = self._prepare_path(path)
        self._validate_banner(banner)
        target.parent.mkdir(parents=True, exist_ok=True)
        export_png(target, banner)

    @staticmethod
    def _prepare_path(path: str | Path) -> Path:
        target = Path(path).expanduser()
        if not str(target):
            raise ValueError("Export path cannot be empty.")
        if target.exists() and target.is_dir():
            raise ValueError(f"Export path points to a directory: {target}")
        return target

    @staticmethod
    def _validate_banner(banner: "Banner") -> None:
        if not banner.lines:
            raise ValueError("Banner has no rendered content to export.")

    @staticmethod
    def _rgb(gradient, ci, nc, li, nl):
        if gradient is None:
            return 0, 255, 255
        t = (
            (ci / (nc - 1) if nc > 1 else 0.0)
            if gradient.direction == "horizontal"
            else (li / (nl - 1) if nl > 1 else 0.0)
        )
        return gradient.color_at(t)

    @staticmethod
    def _rgb_to_hex(rgb) -> str:
        r, g2, b = rgb
        return f"#{r:02x}{g2:02x}{b:02x}"
