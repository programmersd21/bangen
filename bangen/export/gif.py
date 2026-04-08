"""Animated GIF export helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from bangen.effects.utils import clamp

if TYPE_CHECKING:
    from bangen.rendering.banner import Banner

MAX_GIF_FRAMES = 300
_TRANSPARENT = (0, 0, 0, 0)
_FONT_SIZE = 18
_PADDING_X = 24
_PADDING_Y = 24


@dataclass(frozen=True, slots=True)
class GifRenderSettings:
    duration: float
    fps: float
    frame_count: int
    frame_duration_ms: int


@dataclass(frozen=True, slots=True)
class FontMetrics:
    cell_width: int
    cell_height: int
    origin_x: int
    origin_y: int


class BannerPixelRenderer:
    """Caches banner layout for repeated pixel-frame rendering."""

    def __init__(self, banner: "Banner") -> None:
        self._banner = banner
        self._height = len(banner.lines)
        self._width = max((len(line) for line in banner.lines), default=1)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def render_frame(self, t: float) -> list[str]:
        return self._banner.frame_lines(t)

    def cell_style(self, lines: list[str], t: float, row: int, col: int, char: str):
        return self._banner.cell_style(lines, t, row, col, char)


def normalize_gif_settings(duration: float, fps: float) -> GifRenderSettings:
    if duration <= 0:
        raise ValueError("Duration must be greater than 0.")
    if fps <= 0:
        raise ValueError("FPS must be greater than 0.")

    effective_fps = min(float(fps), MAX_GIF_FRAMES / float(duration))
    frame_count = max(1, min(MAX_GIF_FRAMES, round(duration * effective_fps)))
    frame_duration_ms = max(1, int(round(1000 / effective_fps)))

    return GifRenderSettings(
        duration=float(duration),
        fps=effective_fps,
        frame_count=frame_count,
        frame_duration_ms=frame_duration_ms,
    )


def export_gif(path: Path, banner: "Banner", duration: float, fps: float) -> None:
    Image, ImageDraw, ImageFont = _pil()
    settings = normalize_gif_settings(duration, fps)
    renderer = BannerPixelRenderer(banner)
    font = load_monospace_font(ImageFont, _FONT_SIZE)
    metrics = measure_font(font)
    image_size = canvas_size(renderer, metrics)

    frames = [
        _rgba_to_gif_frame(
            Image,
            render_rgba_frame(
                Image=Image,
                ImageDraw=ImageDraw,
                renderer=renderer,
                font=font,
                metrics=metrics,
                image_size=image_size,
                t=frame_index / settings.fps,
            ),
        )
        for frame_index in range(settings.frame_count)
    ]

    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / settings.fps),
        loop=0,
        transparency=255,
        disposal=2,
        optimize=False,
    )


def canvas_size(renderer: BannerPixelRenderer, metrics: FontMetrics) -> tuple[int, int]:
    return (
        max(1, renderer.width * metrics.cell_width + (_PADDING_X * 2)),
        max(1, renderer.height * metrics.cell_height + (_PADDING_Y * 2)),
    )


def render_rgba_frame(
    *,
    Image,
    ImageDraw,
    renderer: BannerPixelRenderer,
    font,
    metrics: FontMetrics,
    image_size: tuple[int, int],
    t: float,
):
    image = Image.new("RGBA", image_size, _TRANSPARENT)
    draw = ImageDraw.Draw(image)
    frame_lines = renderer.render_frame(t)

    for row, line in enumerate(frame_lines):
        for col, char in enumerate(line):
            if char == " ":
                continue
            style = renderer.cell_style(frame_lines, t, row, col, char)
            if style.opacity <= 0.01:
                continue

            for layer in style.overlays:
                layer_alpha = int(round(255 * clamp(style.opacity * layer.alpha)))
                if layer_alpha <= 0:
                    continue
                layer_color = layer.color or style.color
                draw.text(
                    (
                        metrics.origin_x + ((col + layer.dx) * metrics.cell_width),
                        metrics.origin_y + ((row + layer.dy) * metrics.cell_height),
                    ),
                    layer.char or char,
                    fill=(*layer_color, layer_alpha),
                    font=font,
                )

            draw.text(
                (
                    metrics.origin_x + (col * metrics.cell_width),
                    metrics.origin_y + (row * metrics.cell_height),
                ),
                char,
                fill=(*style.color, int(round(255 * style.opacity))),
                font=font,
            )

    return image


def measure_font(font) -> FontMetrics:
    bbox = font.getbbox("M")
    ascent, descent = font.getmetrics()
    cell_width = max(1, bbox[2] - bbox[0])
    cell_height = max(1, ascent + descent)
    origin_x = _PADDING_X - min(0, bbox[0])
    origin_y = _PADDING_Y - min(0, bbox[1])
    return FontMetrics(
        cell_width=cell_width,
        cell_height=cell_height,
        origin_x=origin_x,
        origin_y=origin_y,
    )


def load_monospace_font(ImageFont, size: int):
    for candidate in _font_candidates():
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rgba_to_gif_frame(Image, image):
    quantize = getattr(Image, "Quantize", None)
    dither = getattr(Image, "Dither", None)
    palette_frame = image.quantize(
        colors=254,
        method=getattr(quantize, "FASTOCTREE", 2),
        dither=getattr(dither, "NONE", 0),
    )

    transparent_mask = image.getchannel("A").point(
        lambda alpha: 255 if alpha == 0 else 0
    )
    palette = palette_frame.getpalette() or []
    if len(palette) < 768:
        palette.extend([0] * (768 - len(palette)))
    palette[255 * 3 : (255 * 3) + 3] = [0, 0, 0]
    palette_frame.putpalette(palette)
    palette_frame.paste(255, mask=transparent_mask)
    palette_frame.info["transparency"] = 255
    palette_frame.info["disposal"] = 2
    return palette_frame


def _font_candidates() -> tuple[Path, ...]:
    local_font = Path(__file__).with_name("DejaVuSansMono.ttf")
    return (
        local_font,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/cour.ttf"),
        Path("C:/Windows/Fonts/lucon.ttf"),
    )


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont

        return Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow is required for GIF export.") from exc
