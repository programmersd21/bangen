"""Export engine: TXT · HTML · PNG · GIF."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bangen.gradients.gradient import Gradient
    from bangen.rendering.banner import Banner


class Exporter:
    """Converts a Banner into various output formats."""

    def export_txt(self, banner: "Banner", path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(banner.raw_text() + "\n", encoding="utf-8")

    def export_html(
        self, banner: "Banner", path: Path, gradient: "Gradient | None" = None
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines_html: list[str] = []
        for li, line in enumerate(banner.lines):
            spans: list[str] = []
            for ci, ch in enumerate(line):
                color = self._hex_color(gradient, ci, len(line), li, len(banner.lines))
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
        path.write_text(html, encoding="utf-8")

    def export_png(
        self, banner: "Banner", path: Path, gradient: "Gradient | None" = None
    ) -> None:
        Image, ImageDraw, ImageFont = self._pil()
        path.parent.mkdir(parents=True, exist_ok=True)
        cw, ch, pad = 8, 16, 20
        lines = banner.lines
        mw = max((len(l) for l in lines), default=1)
        img = Image.new(
            "RGB", (mw * cw + pad * 2, len(lines) * ch + pad * 2), (10, 10, 10)
        )
        draw = ImageDraw.Draw(img)
        font = self._font(ImageFont, 14)
        for li, line in enumerate(lines):
            for ci, c in enumerate(line):
                r, g, b = self._rgb(gradient, ci, len(line), li, len(lines))
                draw.text((pad + ci * cw, pad + li * ch), c, fill=(r, g, b), font=font)
        img.save(str(path), "PNG")

    def export_gif(
        self,
        banner: "Banner",
        path: Path,
        gradient: "Gradient | None" = None,
        duration_s: float = 3.0,
        fps: float = 15.0,
        t_start: float = 0.0,
    ) -> None:
        Image, ImageDraw, ImageFont = self._pil()
        from bangen.effects.base import BrightnessModifier

        path.parent.mkdir(parents=True, exist_ok=True)
        cw, ch, pad = 8, 16, 20
        base = banner.lines
        mw = max((len(l) for l in base), default=1)
        ww, hh = mw * cw + pad * 2, len(base) * ch + pad * 2
        pf = self._font(ImageFont, 14)
        frames = []
        for fi in range(max(1, int(duration_s * fps))):
            t = t_start + fi / fps
            lines = list(base)
            brightness = 1.0
            for effect in banner._effects:
                lines = effect.apply(lines, t)
                if isinstance(effect, BrightnessModifier):
                    brightness = effect.brightness(t)
            img = Image.new("RGB", (ww, hh), (10, 10, 10))
            draw = ImageDraw.Draw(img)
            for li, line in enumerate(lines):
                for ci, c in enumerate(line):
                    r, g, b = self._rgb(gradient, ci, len(line), li, len(lines))
                    r, g, b = (
                        min(255, round(r * brightness)),
                        min(255, round(g * brightness)),
                        min(255, round(b * brightness)),
                    )
                    draw.text(
                        (pad + ci * cw, pad + li * ch), c, fill=(r, g, b), font=pf
                    )
            frames.append(img)
        if frames:
            frames[0].save(
                str(path),
                save_all=True,
                append_images=frames[1:],
                loop=0,
                duration=round(1000 / fps),
                optimize=False,
            )

    @staticmethod
    def _pil():
        try:
            from PIL import Image, ImageDraw, ImageFont

            return Image, ImageDraw, ImageFont
        except ImportError:
            raise RuntimeError("Pillow required: pip install Pillow")

    @staticmethod
    def _font(ImageFont, size: int):
        for p in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "C:/Windows/Fonts/cour.ttf",
        ]:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
        return ImageFont.load_default()

    @staticmethod
    def _rgb(g, ci, nc, li, nl):
        if g is None:
            return 0, 255, 255
        t = (
            (ci / (nc - 1) if nc > 1 else 0.0)
            if g.direction == "horizontal"
            else (li / (nl - 1) if nl > 1 else 0.0)
        )
        return g.color_at(t)

    def _hex_color(self, g, ci, nc, li, nl) -> str:
        r, g2, b = self._rgb(g, ci, nc, li, nl)
        return f"#{r:02x}{g2:02x}{b:02x}"
