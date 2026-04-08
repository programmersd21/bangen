"""Distortion-tier effects."""

from __future__ import annotations

import math

from bangen.effects.base import Effect, RasterLayer
from bangen.effects.utils import (
    blend_colors,
    canvas_to_lines,
    empty_canvas,
    hash_noise,
    padded_lines,
    place,
    quantized_time,
    scale_color,
    signed_noise,
)

_GLITCH_CHARS = "!@#$%^&*<>[]{}|\\/?~`=+-"
_NOISE_CHARS = ".,:;*+x#%@$"
_PARTICLE_CHARS = ".,:*+"


class GlitchEffect(Effect):
    tier = "distortion"

    def __init__(
        self,
        config=None,
        intensity: float = 0.05,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.intensity = intensity

    @property
    def name(self) -> str:
        return "glitch"

    def apply(self, lines: list[str], t: float) -> list[str]:
        tick = quantized_time(t, self.config.speed, rate=24.0)
        effective = min(1.0, self.intensity * max(self.config.amplitude, 0.1))
        result: list[str] = []
        for row, line in enumerate(lines):
            chars: list[str] = []
            for col, char in enumerate(line):
                if char != " " and hash_noise(tick, row, col) < effective:
                    index = int(hash_noise(tick, row, col, 9.0) * len(_GLITCH_CHARS))
                    chars.append(_GLITCH_CHARS[index % len(_GLITCH_CHARS)])
                else:
                    chars.append(char)
            result.append("".join(chars))
        return result


class ChromaticAberrationEffect(Effect):
    tier = "distortion"

    @property
    def name(self) -> str:
        return "chromatic_aberration"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        result: list[str] = []
        for row, line in enumerate(padded):
            offset = round(
                math.sin((row * 0.65) + (t * self.config.speed * 2.0))
                * self.config.amplitude
                * 0.5
            )
            if offset > 0:
                result.append((" " * offset + line)[:width])
            elif offset < 0:
                result.append(line[-offset:] + (" " * (-offset)))
            else:
                result.append(line)
        return result

    def colorize(
        self,
        color,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
    ):
        del t, row, col, char, lines
        return scale_color(color, 0.78)

    def raster_layers(
        self,
        *,
        t: float,
        row: int,
        col: int,
        char: str,
        lines: list[str],
        color,
        opacity: float,
    ) -> tuple[RasterLayer, ...]:
        del row, col, lines
        if char == " " or opacity <= 0.01:
            return ()
        shift = max(1, round(self.config.amplitude))
        phase = 1 if math.sin(t * self.config.speed * 2.8) >= 0 else -1
        red = blend_colors(color, (255, 32, 96), 0.55)
        cyan = blend_colors(color, (32, 224, 255), 0.55)
        return (
            RasterLayer(dx=-shift * phase, dy=0, color=red, alpha=0.36),
            RasterLayer(dx=shift * phase, dy=0, color=cyan, alpha=0.36),
        )


class NoiseInjectionEffect(Effect):
    tier = "distortion"

    @property
    def name(self) -> str:
        return "noise_injection"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = [list(line) for line in padded]
        tick = quantized_time(t, self.config.speed, rate=18.0)
        density = 0.015 * max(self.config.amplitude, 0.25)

        for row in range(height):
            for col in range(width):
                if canvas[row][col] != " ":
                    continue
                if hash_noise(tick, row, col, 7.0) >= density:
                    continue
                neighbors = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny = row + dy
                        nx = col + dx
                        if 0 <= ny < height and 0 <= nx < width and padded[ny][nx] != " ":
                            neighbors += 1
                if neighbors:
                    idx = int(hash_noise(tick, row, col, 19.0) * len(_NOISE_CHARS))
                    canvas[row][col] = _NOISE_CHARS[idx % len(_NOISE_CHARS)]

        return canvas_to_lines(canvas)


class MeltEffect(Effect):
    tier = "distortion"

    @property
    def name(self) -> str:
        return "melt"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        for col in range(width):
            drip = max(
                0,
                round(
                    (
                        math.sin((col * self.config.frequency) + (t * self.config.speed))
                        + 1.0
                    )
                    * 0.5
                    * self.config.amplitude
                ),
            )
            for row in range(height):
                char = padded[row][col]
                if char == " ":
                    continue
                target_row = min(height - 1, row + drip)
                place(canvas, col, target_row, char)
                for trail in range(row + 1, target_row):
                    if canvas[trail][col] == " ":
                        place(canvas, col, trail, "|")
        return canvas_to_lines(canvas)


class WarpEffect(Effect):
    tier = "distortion"

    @property
    def name(self) -> str:
        return "warp"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        for row, line in enumerate(padded):
            for col, char in enumerate(line):
                if char == " ":
                    continue
                dx = round(
                    math.sin((row * self.config.frequency) + (t * self.config.speed))
                    * self.config.amplitude
                )
                dy = round(
                    math.cos((col * self.config.frequency * 0.5) - (t * self.config.speed))
                    * (self.config.amplitude * 0.5)
                )
                place(canvas, col + dx, row + dy, char)
        return canvas_to_lines(canvas)


class FragmentEffect(Effect):
    tier = "distortion"

    def __init__(
        self,
        config=None,
        chunk_width: int = 6,
        **_: object,
    ) -> None:
        super().__init__(config)
        self.chunk_width = chunk_width

    @property
    def name(self) -> str:
        return "fragment"

    def apply(self, lines: list[str], t: float) -> list[str]:
        padded, width, _ = padded_lines(lines)
        result: list[str] = []
        for row, line in enumerate(padded):
            chars = [" "] * width
            for start in range(0, width, self.chunk_width):
                chunk = line[start : start + self.chunk_width]
                chunk_index = start // self.chunk_width
                offset = round(
                    math.sin(
                        (chunk_index * self.config.frequency)
                        + (row * 0.4)
                        + (t * self.config.speed)
                    )
                    * self.config.amplitude
                )
                for index, char in enumerate(chunk):
                    dest = start + index + offset
                    if 0 <= dest < width and char != " ":
                        chars[dest] = char
            result.append("".join(chars))
        return result


class ParticleDisintegrationEffect(Effect):
    tier = "signature"

    @property
    def name(self) -> str:
        return "particle_disintegration"

    def apply(self, lines: list[str], t: float) -> list[str]:
        progress = min(1.0, t * self.config.speed * 0.22)
        padded, width, height = padded_lines(lines)
        canvas = empty_canvas(width, height)
        spread = max(1.0, self.config.amplitude * max(width, height) * 0.12)

        for row, line in enumerate(padded):
            for col, char in enumerate(line):
                if char == " ":
                    continue
                seed = hash_noise(row, col, 17.0)
                if seed > progress:
                    place(canvas, col, row, char)
                    continue
                vx = signed_noise(row, col, 23.0) * spread
                vy = signed_noise(row, col, 41.0) * spread
                target_col = round(col + (vx * progress))
                target_row = round(row + (vy * progress) - (progress * 2.0))
                particle_index = int(hash_noise(row, col, progress, 55.0) * len(_PARTICLE_CHARS))
                place(
                    canvas,
                    target_col,
                    target_row,
                    _PARTICLE_CHARS[particle_index % len(_PARTICLE_CHARS)],
                )

        return canvas_to_lines(canvas)
