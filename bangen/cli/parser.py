"""argparse CLI definition."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bangen",
        description="Bangen v2 — ASCII banner rendering engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bangen "HELLO"
  bangen "HELLO" --font slant --gradient "#ff00ff:#00ffff"
  bangen "HELLO" --effect wave --effect chromatic_aberration --effect pulse --speed 1.5
  bangen "HELLO" --screensaver
  bangen --preset neon_wave "HELLO"
  bangen --preset-file ./preset.json "HELLO"
  bangen "HELLO" --ai "cyberpunk neon hacker vibe"
  bangen "HELLO" --export-png banner.png --export-gif banner.gif
  bangen --list-effects
  bangen --list-presets
  bangen --list-fonts
""",
    )
    p.add_argument("text", nargs="?", help="Text to render")
    p.add_argument("--font", "-f", default=None)
    p.add_argument(
        "--gradient",
        "-g",
        default=None,
        help="Colon-separated hex stops: '#ff00ff:#00ffff'",
    )
    p.add_argument(
        "--gradient-dir",
        choices=["horizontal", "vertical"],
        default=None,
        help="Gradient direction. When omitted, uses preset/AI suggestion value (or defaults to 'horizontal').",
    )
    p.add_argument(
        "--effect",
        "-e",
        action="append",
        dest="effects",
        default=None,
        help="Effect name (repeatable). Use --list-effects to inspect the full library.",
    )
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--amplitude", type=float, default=1.0)
    p.add_argument("--frequency", type=float, default=1.0)
    p.add_argument("--preset", "-p", default=None)
    p.add_argument(
        "--preset-file",
        metavar="PATH",
        default=None,
        help="Load a preset JSON from a custom file path (does not save it).",
    )
    p.add_argument("--list-presets", action="store_true")
    p.add_argument("--list-fonts", action="store_true")
    p.add_argument("--list-effects", action="store_true")
    p.add_argument("--export-txt", metavar="PATH")
    p.add_argument("--export-html", metavar="PATH")
    p.add_argument("--export-png", metavar="PATH")
    p.add_argument("--export-gif", metavar="PATH")
    p.add_argument("--gif-duration", type=float, default=3.0)
    p.add_argument("--gif-fps", type=float, default=15.0)
    p.add_argument("--animate", action="store_true")
    p.add_argument("--animate-duration", type=float, default=5.0)
    p.add_argument(
        "--screensaver",
        action="store_true",
        help="Run full-screen screensaver mode with auto-fitted text and rotating randomized effect scenes.",
    )
    p.add_argument(
        "--screensaver-duration",
        type=float,
        default=0.0,
        help="Optional total screensaver runtime in seconds. Defaults to 0 for infinite until Ctrl+C.",
    )
    p.add_argument(
        "--screensaver-seed",
        type=int,
        default=None,
        help="Seed screensaver randomization for reproducible effect rotations.",
    )
    p.add_argument("--ai", metavar="PROMPT")
    p.add_argument("--save-preset", metavar="NAME")
    p.add_argument("--font-dir", metavar="DIR")
    p.add_argument("--no-border", action="store_true")
    p.add_argument("--title", default=None)
    p.add_argument("--static", action="store_true")
    return p


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def has_cli_args(argv: list[str] | None = None) -> bool:
    args = argv if argv is not None else sys.argv[1:]
    return len(args) > 0
