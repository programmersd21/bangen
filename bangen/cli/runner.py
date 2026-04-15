"""CLI command runner."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from bangen.cli.screensaver import run_screensaver
from bangen.effects import AVAILABLE_EFFECTS, EFFECT_TIERS, EffectConfig, build_effect
from bangen.export.exporter import Exporter
from bangen.gradients.gradient import Gradient
from bangen.presets.manager import Preset, PresetManager
from bangen.rendering.engine import DEFAULT_FONT, RenderEngine
from bangen.rendering.sizing import calculate_auto_size, format_size_info


def run_cli(args) -> None:
    console = Console()
    exporter = Exporter()

    font_dirs = [Path(args.font_dir)] if args.font_dir else []
    engine = RenderEngine(font_dirs=font_dirs)
    preset_manager = PresetManager()

    # ---- list commands ------------------------------------------------
    if args.list_presets:
        _list_presets(console, preset_manager)
        return

    if args.list_fonts:
        _list_fonts(console, engine)
        return

    if args.list_effects:
        _list_effects(console)
        return

    # ---- resolve text -------------------------------------------------
    text = args.text
    if not text:
        console.print("[red]Error:[/red] text argument is required.")
        sys.exit(1)

    # ---- load preset --------------------------------------------------
    preset: Preset | None = None
    if args.preset_file:
        try:
            preset = preset_manager.load_file(Path(args.preset_file))
        except Exception as exc:
            console.print(f"[red]Error:[/red] failed to load preset file — {exc}")
            sys.exit(2)
    elif args.preset:
        preset = preset_manager.get(args.preset)
        if preset is None:
            console.print(
                f"[yellow]Warning:[/yellow] preset {args.preset!r} not found."
            )

    # ---- AI suggestion ------------------------------------------------
    if args.ai:
        from bangen.ai.suggester import suggest_from_prompt

        s = suggest_from_prompt(args.ai)
        font = args.font or s.font
        gradient_str = args.gradient or s.gradient
        gradient_dir = args.gradient_dir or s.gradient_direction or "horizontal"
        effects_list: list[str] = args.effects or s.effects
        effect_cfg_map: dict = s.effect_config
    elif preset:
        font = args.font or preset.font
        gradient_str = args.gradient or preset.gradient
        gradient_dir = args.gradient_dir or preset.gradient_direction or "horizontal"
        effects_list = args.effects or list(preset.effects)
        effect_cfg_map = dict(preset.effect_config)
    else:
        font = args.font or DEFAULT_FONT
        gradient_str = args.gradient or "#00ffff:#ff00ff"
        gradient_dir = args.gradient_dir or "horizontal"
        effects_list = args.effects or []
        effect_cfg_map = {}

    if args.screensaver:
        if any((args.export_txt, args.export_png, args.export_gif)):
            console.print(
                "[yellow]Warning:[/yellow] export flags are ignored in screensaver mode."
            )
        run_screensaver(
            console,
            engine,
            text=text,
            preferred_font=font,
            preferred_gradient=gradient_str,
            preferred_gradient_direction=gradient_dir,
            seed=args.screensaver_seed,
            duration=args.screensaver_duration or None,
        )
        return

    # ---- render -------------------------------------------------------
    banner = engine.render(text, font)

    # ---- gradient -----------------------------------------------------
    gradient: Gradient | None = None
    try:
        gradient = Gradient.from_string(gradient_str, direction=gradient_dir)
        banner.set_gradient(gradient)
    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] gradient parse error — {exc}")

    # ---- effects ------------------------------------------------------
    for ename in effects_list:
        ecfg_data = effect_cfg_map.get(ename, {})
        cfg = EffectConfig(
            speed=ecfg_data.get("speed", args.speed),
            amplitude=ecfg_data.get("amplitude", args.amplitude),
            frequency=ecfg_data.get("frequency", args.frequency),
        )
        kwargs = {
            key: value
            for key, value in ecfg_data.items()
            if key not in {"speed", "amplitude", "frequency"}
        }
        try:
            banner.apply(build_effect(ename, config=cfg, **kwargs))
        except ValueError as exc:
            console.print(f"[yellow]Warning:[/yellow] {exc}")

    # ---- exports ------------------------------------------------------
    if args.export_txt:
        try:
            _export_with_progress(
                console,
                label="TXT",
                target=args.export_txt,
                work=lambda callback: exporter.export_txt(
                    banner,
                    Path(args.export_txt),
                    progress_callback=callback,
                ),
            )
            console.print(f"[green]TXT ->[/green] {args.export_txt}")
        except Exception as exc:
            console.print(f"[red]{exc}[/red]")

    if args.export_png:
        try:
            _export_with_progress(
                console,
                label="PNG",
                target=args.export_png,
                work=lambda callback: exporter.export_png(
                    banner,
                    Path(args.export_png),
                    progress_callback=callback,
                ),
            )
            console.print(f"[green]PNG ->[/green] {args.export_png}")
        except Exception as exc:
            console.print(f"[red]{exc}[/red]")

    if args.export_gif:
        try:
            _export_with_progress(
                console,
                label="GIF",
                target=args.export_gif,
                work=lambda callback: exporter.export_gif(
                    banner,
                    Path(args.export_gif),
                    duration=args.gif_duration,
                    fps=args.gif_fps,
                    progress_callback=callback,
                ),
            )
            console.print(f"[green]GIF ->[/green] {args.export_gif}")
        except Exception as exc:
            console.print(f"[red]{exc}[/red]")

    # ---- save preset --------------------------------------------------
    if args.save_preset:
        p = Preset(
            name=args.save_preset,
            font=font,
            gradient=gradient_str,
            gradient_direction=gradient_dir,
            effects=effects_list,
            effect_config=effect_cfg_map,
        )
        preset_manager.save(p)
        console.print(f"[green]Preset {args.save_preset!r} saved.[/green]")

    # ---- terminal display --------------------------------------------
    show_border = not args.no_border
    animate = args.animate and not args.static and bool(effects_list)

    # ---- auto-size calculation ----------------------------------------
    size_config = None
    if args.auto_size:
        try:
            size_config = calculate_auto_size(banner)
            console.print(f"[dim]{format_size_info(size_config, banner)}[/dim]")
        except Exception as exc:
            console.print(
                f"[yellow]Warning:[/yellow] auto-size calculation failed — {exc}"
            )

    if animate:
        t0 = time.monotonic()
        dur = args.animate_duration
        with Live(console=console, refresh_per_second=20, screen=False) as live:
            while time.monotonic() - t0 < dur:
                t = time.monotonic() - t0
                frame = banner.render_frame(t)
                live.update(_wrap(frame, show_border, args.title))
                time.sleep(0.05)
    else:
        frame = banner.render_frame(0.0)
        console.print(_wrap(frame, show_border, args.title))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap(content, border: bool, title: str | None):
    if border:
        return Panel(content, border_style="cyan", box=box.ROUNDED, title=title)
    return content


def _export_with_progress(console: Console, *, label: str, target: str, work) -> None:
    progress = Progress(
        TextColumn("[bold cyan]{task.fields[label]}[/bold cyan]"),
        TextColumn("{task.fields[bar]}"),
        TaskProgressColumn(),
        TextColumn("{task.fields[status]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )
    with progress:
        task_id = progress.add_task(
            "export",
            total=100,
            completed=0,
            label=f"{label} export",
            bar=_ascii_bar(0.0),
            status=f"Preparing {target}",
        )

        def report(fraction: float, status: str) -> None:
            completed = max(0.0, min(100.0, fraction * 100.0))
            progress.update(
                task_id,
                completed=completed,
                bar=_ascii_bar(completed / 100.0),
                status=status,
            )
            progress.refresh()

        work(report)
        progress.update(
            task_id,
            completed=100.0,
            bar=_ascii_bar(1.0),
            status="Done",
        )


def _ascii_bar(fraction: float, width: int = 32) -> str:
    fraction = max(0.0, min(1.0, fraction))
    filled = min(width, max(0, round(fraction * width)))
    return f"[{'=' * filled}{'-' * (width - filled)}]"


def _list_presets(console: Console, mgr: PresetManager) -> None:
    t = Table(title="Available Presets", box=box.ROUNDED, border_style="cyan")
    t.add_column("Name", style="bold cyan")
    t.add_column("Font")
    t.add_column("Gradient")
    t.add_column("Effects")
    for name, preset in sorted(mgr.list_presets().items()):
        t.add_row(name, preset.font, preset.gradient, ", ".join(preset.effects) or "—")
    console.print(t)


def _list_fonts(console: Console, engine: RenderEngine) -> None:
    fonts = sorted(engine.available_fonts())
    t = Table(
        title=f"Available Fonts ({len(fonts)})", box=box.ROUNDED, border_style="cyan"
    )
    t.add_column("Font Name")
    for f in fonts:
        t.add_row(f)
    console.print(t)


def _list_effects(console: Console) -> None:
    table = Table(title="Effect Library", box=box.ROUNDED, border_style="cyan")
    table.add_column("Tier", style="bold magenta")
    table.add_column("Effects", style="white")
    for tier_name, effects in EFFECT_TIERS.items():
        table.add_row(tier_name.title(), ", ".join(effects))
    table.caption = f"{len(AVAILABLE_EFFECTS)} effects"
    console.print(table)
