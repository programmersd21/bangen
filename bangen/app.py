"""Bangen v2 — entry point."""

from __future__ import annotations


def main() -> None:
    from bangen.cli.parser import has_cli_args, parse_args

    if has_cli_args():
        args = parse_args()
        from bangen.cli.runner import run_cli

        run_cli(args)
    else:
        from bangen.presets.manager import PresetManager
        from bangen.rendering.engine import RenderEngine
        from bangen.tui.app import TUIApp

        engine = RenderEngine()
        pm = PresetManager()
        app = TUIApp(engine, pm)
        app.run()
