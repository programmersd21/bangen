"""Auto-sizing engine for banners based on text and terminal dimensions."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bangen.rendering.banner import Banner


@dataclass(frozen=True, slots=True)
class SizeConfig:
    """Calculated size configuration for rendering."""

    max_width: int
    max_height: int
    scale_factor: float
    padding_x: int
    padding_y: int


def get_terminal_size() -> tuple[int, int]:
    """Get current terminal width and height."""
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    return cols, rows


def calculate_auto_size(
    banner: "Banner",
    preserve_aspect: bool = True,
    padding_percent: float = 0.1,
) -> SizeConfig:
    """
    Calculate optimal sizing for the banner based on terminal and text dimensions.

    Args:
        banner: The banner to size
        preserve_aspect: If True, maintains banner aspect ratio
        padding_percent: Padding as percentage of terminal size (0.0-1.0)

    Returns:
        SizeConfig with calculated dimensions and scaling
    """
    term_width, term_height = get_terminal_size()

    # Calculate usable space accounting for padding
    padding_x = max(2, int(term_width * padding_percent))
    padding_y = max(1, int(term_height * padding_percent))

    available_width = term_width - (padding_x * 2)
    available_height = term_height - (padding_y * 2)

    # Get banner dimensions
    banner_width = banner.width()
    banner_height = banner.height()

    if banner_width == 0 or banner_height == 0:
        return SizeConfig(
            max_width=available_width,
            max_height=available_height,
            scale_factor=1.0,
            padding_x=padding_x,
            padding_y=padding_y,
        )

    # Calculate scale to fit terminal
    scale_by_width = available_width / banner_width
    scale_by_height = available_height / banner_height

    if preserve_aspect:
        scale_factor = min(scale_by_width, scale_by_height, 1.0)
    else:
        scale_factor = min(scale_by_width, 1.0)

    # Ensure minimum scale (don't shrink too much)
    scale_factor = max(0.5, scale_factor)

    max_width = int(banner_width * scale_factor)
    max_height = int(banner_height * scale_factor)

    return SizeConfig(
        max_width=max(10, max_width),
        max_height=max(3, max_height),
        scale_factor=scale_factor,
        padding_x=padding_x,
        padding_y=padding_y,
    )


def apply_size_config_to_export(
    text: str,
    config: SizeConfig,
) -> dict:
    """
    Convert size config to export parameters.

    This creates appropriate sizing info for exports.
    """
    return {
        "canvas_width": config.max_width,
        "canvas_height": config.max_height,
        "scale_factor": config.scale_factor,
        "padding_x": config.padding_x,
        "padding_y": config.padding_y,
    }


def format_size_info(config: SizeConfig, banner: Banner) -> str:
    """Format size configuration as human-readable text."""
    return (
        f"Auto-size | Text: {banner.width()}x{banner.height()} | "
        f"Canvas: {config.max_width}x{config.max_height} | "
        f"Scale: {config.scale_factor:.2f}x | "
        f"Padding: ({config.padding_x}, {config.padding_y})"
    )
