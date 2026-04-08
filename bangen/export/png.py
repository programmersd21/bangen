"""Static PNG export helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bangen.export.gif import (
    BannerPixelRenderer,
    canvas_size,
    load_monospace_font,
    measure_font,
    render_rgba_frame,
)

if TYPE_CHECKING:
    from bangen.rendering.banner import Banner

_FONT_SIZE = 18


def export_png(path: Path, banner: "Banner") -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for PNG export.") from exc

    renderer = BannerPixelRenderer(banner)
    font = load_monospace_font(ImageFont, _FONT_SIZE)
    metrics = measure_font(font)
    image = render_rgba_frame(
        Image=Image,
        ImageDraw=ImageDraw,
        renderer=renderer,
        font=font,
        metrics=metrics,
        image_size=canvas_size(renderer, metrics),
        t=0.0,
    )
    image.save(path, "PNG")
