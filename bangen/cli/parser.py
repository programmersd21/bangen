"""Typer-based CLI definition."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Annotated

import typer
import typer.rich_utils as typer_rich_utils

setattr(typer_rich_utils, "RICH_HELP", True)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=False,
    help="Bangen v2 - ASCII banner rendering engine",
    epilog=(
        "Examples:\n"
        '  bangen "HELLO"\n'
        '  bangen "HELLO" --font slant --gradient "#ff00ff:#00ffff"\n'
        '  bangen "HELLO" --effect wave --effect chromatic_aberration --effect pulse --speed 1.5\n'
        '  bangen "HELLO" --screensaver\n'
        '  bangen --preset neon_wave "HELLO"\n'
        '  bangen --preset-file ./preset.json "HELLO"\n'
        '  bangen "HELLO" --ai "cyberpunk neon hacker vibe"\n'
        '  bangen "HELLO" --export-png banner.png\n'
        '  bangen "HELLO" --export-gif banner.gif\n'
        "  bangen --list-effects\n"
        "  bangen --list-presets\n"
        "  bangen --list-fonts"
    ),
)


def has_cli_args(argv: list[str] | None = None) -> bool:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    return len(args) > 0


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": False}
)
def main(
    ctx: typer.Context,
    font: Annotated[str | None, typer.Option("--font", "-f")] = None,
    gradient: Annotated[
        str | None,
        typer.Option(
            "--gradient", "-g", help="Colon-separated hex stops: '#ff00ff:#00ffff'"
        ),
    ] = None,
    gradient_dir: Annotated[
        str | None,
        typer.Option(
            "--gradient-dir",
            help="Gradient direction. When omitted, uses preset/AI suggestion value (or defaults to 'horizontal').",
            case_sensitive=False,
        ),
    ] = None,
    effects: Annotated[
        list[str] | None,
        typer.Option(
            "--effect",
            "-e",
            help="Effect name (repeatable). Use --list-effects to inspect the full library.",
        ),
    ] = None,
    speed: Annotated[float, typer.Option("--speed")] = 1.0,
    amplitude: Annotated[float, typer.Option("--amplitude")] = 1.0,
    frequency: Annotated[float, typer.Option("--frequency")] = 1.0,
    preset: Annotated[str | None, typer.Option("--preset", "-p")] = None,
    preset_file: Annotated[
        str | None,
        typer.Option(
            "--preset-file",
            metavar="PATH",
            help="Load a preset JSON from a custom file path (does not save it).",
        ),
    ] = None,
    list_presets: Annotated[bool, typer.Option("--list-presets")] = False,
    list_fonts: Annotated[bool, typer.Option("--list-fonts")] = False,
    list_effects: Annotated[bool, typer.Option("--list-effects")] = False,
    export_txt: Annotated[
        str | None, typer.Option("--export-txt", metavar="PATH")
    ] = None,
    export_png: Annotated[
        str | None, typer.Option("--export-png", metavar="PATH")
    ] = None,
    export_gif: Annotated[
        str | None, typer.Option("--export-gif", metavar="PATH")
    ] = None,
    gif_duration: Annotated[float, typer.Option("--gif-duration")] = 3.0,
    gif_fps: Annotated[float, typer.Option("--gif-fps")] = 15.0,
    animate: Annotated[bool, typer.Option("--animate")] = False,
    animate_duration: Annotated[float, typer.Option("--animate-duration")] = 5.0,
    screensaver: Annotated[
        bool,
        typer.Option(
            "--screensaver",
            help="Run full-screen screensaver mode with auto-fitted text and rotating randomized effect scenes.",
        ),
    ] = False,
    screensaver_duration: Annotated[
        float,
        typer.Option(
            "--screensaver-duration",
            help="Optional total screensaver runtime in seconds. Defaults to 0 for infinite until Ctrl+C.",
        ),
    ] = 0.0,
    screensaver_seed: Annotated[
        int | None,
        typer.Option(
            "--screensaver-seed",
            help="Seed screensaver randomization for reproducible effect rotations.",
        ),
    ] = None,
    ai: Annotated[str | None, typer.Option("--ai", metavar="PROMPT")] = None,
    save_preset: Annotated[
        str | None, typer.Option("--save-preset", metavar="NAME")
    ] = None,
    font_dir: Annotated[str | None, typer.Option("--font-dir", metavar="DIR")] = None,
    no_border: Annotated[bool, typer.Option("--no-border")] = False,
    title: Annotated[str | None, typer.Option("--title")] = None,
    static: Annotated[bool, typer.Option("--static")] = False,
    auto_size: Annotated[
        bool,
        typer.Option(
            "--auto-size/--no-auto-size",
            help="Enable/disable auto-sizing (enabled by default). Auto-adjust banner width/height based on terminal and text size.",
        ),
    ] = True,
) -> None:
    from bangen.cli.runner import run_cli

    extra_args = list(ctx.args)
    text = None
    if extra_args:
        if len(extra_args) > 1:
            raise typer.BadParameter("Only one text argument may be provided.")
        text = extra_args[0]

    if gradient_dir is not None:
        gradient_dir = gradient_dir.lower()
        if gradient_dir not in {"horizontal", "vertical"}:
            raise typer.BadParameter(
                "Gradient direction must be 'horizontal' or 'vertical'."
            )

    args = SimpleNamespace(
        text=text,
        font=font,
        gradient=gradient,
        gradient_dir=gradient_dir,
        effects=effects or None,
        speed=speed,
        amplitude=amplitude,
        frequency=frequency,
        preset=preset,
        preset_file=preset_file,
        list_presets=list_presets,
        list_fonts=list_fonts,
        list_effects=list_effects,
        export_txt=export_txt,
        export_png=export_png,
        export_gif=export_gif,
        gif_duration=gif_duration,
        gif_fps=gif_fps,
        animate=animate,
        animate_duration=animate_duration,
        screensaver=screensaver,
        screensaver_duration=screensaver_duration,
        screensaver_seed=screensaver_seed,
        ai=ai,
        save_preset=save_preset,
        font_dir=font_dir,
        no_border=no_border,
        title=title,
        static=static,
        auto_size=auto_size,
    )
    run_cli(args)
