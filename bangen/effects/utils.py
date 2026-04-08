"""Shared effect math helpers."""

from __future__ import annotations

import colorsys
import math
from typing import Iterable

from bangen.effects.base import RGB


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    x = clamp((value - edge0) / (edge1 - edge0))
    return x * x * (3.0 - 2.0 * x)


def scale_color(color: RGB, factor: float) -> RGB:
    return tuple(max(0, min(255, round(channel * factor))) for channel in color)  # type: ignore[return-value]


def blend_colors(a: RGB, b: RGB, t: float) -> RGB:
    ratio = clamp(t)
    return (
        round(lerp(a[0], b[0], ratio)),
        round(lerp(a[1], b[1], ratio)),
        round(lerp(a[2], b[2], ratio)),
    )


def shift_hue(color: RGB, amount: float) -> RGB:
    r, g, b = [channel / 255.0 for channel in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r2, g2, b2 = colorsys.hsv_to_rgb((h + amount) % 1.0, s, v)
    return round(r2 * 255), round(g2 * 255), round(b2 * 255)


def palette_color(stops: Iterable[RGB], t: float) -> RGB:
    colors = list(stops)
    if not colors:
        return (255, 255, 255)
    if len(colors) == 1:
        return colors[0]
    x = clamp(t) * (len(colors) - 1)
    index = min(len(colors) - 2, max(0, int(x)))
    local = x - index
    return blend_colors(colors[index], colors[index + 1], local)


def hash_noise(*values: float) -> float:
    accumulator = 0.0
    for index, value in enumerate(values, start=1):
        accumulator += value * (12.9898 + index * 7.233)
    raw = math.sin(accumulator) * 43758.5453
    return raw - math.floor(raw)


def signed_noise(*values: float) -> float:
    return (hash_noise(*values) * 2.0) - 1.0


def quantized_time(t: float, speed: float, rate: float = 24.0) -> float:
    return math.floor(t * max(speed, 0.01) * rate)


def padded_lines(lines: list[str]) -> tuple[list[str], int, int]:
    height = len(lines)
    width = max((len(line) for line in lines), default=0)
    return [line.ljust(width) for line in lines], width, height


def empty_canvas(width: int, height: int) -> list[list[str]]:
    return [[" " for _ in range(max(0, width))] for _ in range(max(0, height))]


def canvas_to_lines(canvas: list[list[str]]) -> list[str]:
    return ["".join(row).rstrip() for row in canvas]


def place(canvas: list[list[str]], x: int, y: int, char: str) -> None:
    if not canvas or not char:
        return
    if 0 <= y < len(canvas) and 0 <= x < len(canvas[y]) and char != " ":
        canvas[y][x] = char
