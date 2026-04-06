"""Full-screen interactive TUI with split controls/preview layout."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Callable

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bangen.effects import AVAILABLE_EFFECTS, EffectConfig, build_effect
from bangen.gradients.gradient import Gradient
from bangen.presets.manager import Preset, PresetManager
from bangen.rendering.engine import PRESET_FONTS, RenderEngine

# ── field indices ──────────────────────────────────────────────────────────
_F_TEXT = 0
_F_FONT = 1
_F_GRAD = 2
_F_DIR = 3
_F_EFX_BASE = 4  # 4..4+len(AVAILABLE_EFFECTS)-1
_F_SPEED = _F_EFX_BASE + len(AVAILABLE_EFFECTS)
_F_AMP = _F_SPEED + 1
_NUM_FIELDS = _F_AMP + 1


@dataclass
class TUIState:
    text: str = "BANGEN"
    font: str = "ansi_shadow"
    font_idx: int = 0
    gradient_str: str = "#00ffff:#ff00ff"
    gradient_dir: str = "horizontal"
    active_effects: list[str] = field(default_factory=list)
    effect_speed: float = 1.0
    effect_amplitude: float = 1.0
    current_field: int = 0
    editing: bool = False
    edit_buffer: str = ""
    running: bool = True
    status: str = ""
    t: float = 0.0


class TUIApp:
    """Keyboard-driven live TUI banner designer."""

    def __init__(self, engine: RenderEngine, preset_manager: PresetManager) -> None:
        self._engine = engine
        self._pm = preset_manager
        self._state = TUIState()
        self._console = Console()

    # ── preset loading ────────────────────────────────────────────────────

    def load_preset(self, preset: Preset) -> None:
        s = self._state
        s.font = preset.font
        try:
            s.font_idx = PRESET_FONTS.index(preset.font)
        except ValueError:
            s.font_idx = 0
        s.gradient_str = preset.gradient
        s.gradient_dir = preset.gradient_direction
        s.active_effects = list(preset.effects)

    def set_text(self, text: str) -> None:
        self._state.text = text

    # ── entry point ───────────────────────────────────────────────────────

    def run(self) -> TUIState:
        if sys.platform == "win32":
            self._run_windows()
        else:
            self._run_unix()
        return self._state

    # ── platform key readers ──────────────────────────────────────────────

    def _run_unix(self) -> None:
        import termios
        import tty

        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            self._event_loop(lambda: self._unix_key(fd))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)

    def _unix_key(self, fd: int) -> str | None:
        import select

        r, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not r:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            import select as sel

            r2, _, _ = sel.select([sys.stdin], [], [], 0.05)
            if r2:
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    r3, _, _ = sel.select([sys.stdin], [], [], 0.05)
                    if r3:
                        ch3 = sys.stdin.read(1)
                        return f"\x1b[{ch3}"
        return ch

    def _run_windows(self) -> None:
        import msvcrt

        _MAP = {b"H": "\x1b[A", b"P": "\x1b[B", b"K": "\x1b[D", b"M": "\x1b[C"}

        def read():
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                return _MAP.get(msvcrt.getch(), "")
            try:
                return ch.decode("utf-8")
            except Exception:
                return None

        self._event_loop(read)

    # ── main loop ─────────────────────────────────────────────────────────

    def _event_loop(self, read_key: Callable[[], str | None]) -> None:
        s = self._state
        t0 = time.monotonic()
        with Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=20,
            screen=True,
        ) as live:
            while s.running:
                s.t = time.monotonic() - t0
                live.update(self._build_layout())
                key = read_key()
                if key:
                    self._handle(key)
                time.sleep(0.05)

    # ── input handling ────────────────────────────────────────────────────

    def _handle(self, key: str) -> None:
        if self._state.editing:
            self._handle_edit(key)
        else:
            self._handle_nav(key)

    def _handle_nav(self, key: str) -> None:
        s = self._state
        if key == "\x1b[A":  # up
            s.current_field = (s.current_field - 1) % _NUM_FIELDS
        elif key == "\x1b[B":  # down
            s.current_field = (s.current_field + 1) % _NUM_FIELDS
        elif key in ("\r", "\n"):
            self._activate()
        elif key == "\x1b[C":  # right
            self._nudge(+1)
        elif key == "\x1b[D":  # left
            self._nudge(-1)
        elif key in ("q", "Q", "\x03", "\x04"):  # q / Ctrl-C / Ctrl-D
            s.running = False
        elif key in ("s", "S"):
            self._quick_save()

    def _handle_edit(self, key: str) -> None:
        s = self._state
        if key in ("\r", "\n"):
            f = s.current_field
            if f == _F_TEXT:
                s.text = s.edit_buffer or s.text
            elif f == _F_GRAD:
                s.gradient_str = s.edit_buffer or s.gradient_str
            s.editing = False
            s.edit_buffer = ""
        elif key == "\x1b":
            s.editing = False
            s.edit_buffer = ""
        elif key in ("\x7f", "\x08"):
            s.edit_buffer = s.edit_buffer[:-1]
        elif key.isprintable():
            s.edit_buffer += key

    def _activate(self) -> None:
        s = self._state
        f = s.current_field
        if f == _F_TEXT:
            s.editing = True
            s.edit_buffer = s.text
        elif f == _F_FONT:
            s.font_idx = (s.font_idx + 1) % len(PRESET_FONTS)
            s.font = PRESET_FONTS[s.font_idx]
        elif f == _F_GRAD:
            s.editing = True
            s.edit_buffer = s.gradient_str
        elif f == _F_DIR:
            s.gradient_dir = (
                "vertical" if s.gradient_dir == "horizontal" else "horizontal"
            )
        elif _F_EFX_BASE <= f < _F_SPEED:
            ename = AVAILABLE_EFFECTS[f - _F_EFX_BASE]
            if ename in s.active_effects:
                s.active_effects.remove(ename)
            else:
                s.active_effects.append(ename)

    def _nudge(self, delta: int) -> None:
        s = self._state
        f = s.current_field
        if f == _F_FONT:
            s.font_idx = (s.font_idx + delta) % len(PRESET_FONTS)
            s.font = PRESET_FONTS[s.font_idx]
        elif f == _F_SPEED:
            s.effect_speed = round(max(0.1, s.effect_speed + delta * 0.1), 2)
        elif f == _F_AMP:
            s.effect_amplitude = round(max(0.1, s.effect_amplitude + delta * 0.1), 2)

    def _quick_save(self) -> None:
        s = self._state
        name = f"tui_{int(time.time())}"
        self._pm.save(
            Preset(
                name=name,
                font=s.font,
                gradient=s.gradient_str,
                gradient_direction=s.gradient_dir,
                effects=list(s.active_effects),
                effect_config={},
            )
        )
        s.status = f"Saved as '{name}'"

    # ── rendering ─────────────────────────────────────────────────────────

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_row(Layout(name="ctrl", ratio=1), Layout(name="prev", ratio=2))
        layout["ctrl"].update(
            Panel(
                self._controls_table(),
                title="[bold cyan]Controls[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
        layout["prev"].update(
            Panel(
                self._preview(),
                title="[bold magenta]Live Preview[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED,
                subtitle=self._help_line(),
            )
        )
        return layout

    def _controls_table(self) -> Table:
        s = self._state
        tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        tbl.add_column("k", no_wrap=True, width=18)
        tbl.add_column("v")

        def row(fi: int, label: str, val: str) -> None:
            sel = s.current_field == fi
            arrow = "▶" if sel else " "
            lstyle = "bold reverse cyan" if sel else "dim"
            vstyle = "bold cyan" if sel else "white"
            tbl.add_row(Text(f"{arrow} {label}", style=lstyle), Text(val, style=vstyle))

        # text
        tv = (
            (s.edit_buffer + "█")
            if (s.editing and s.current_field == _F_TEXT)
            else s.text
        )
        row(_F_TEXT, "Text", tv)

        # font
        row(_F_FONT, "Font", s.font)

        # gradient
        gv = (
            (s.edit_buffer + "█")
            if (s.editing and s.current_field == _F_GRAD)
            else s.gradient_str
        )
        row(_F_GRAD, "Gradient", gv)

        # direction
        row(_F_DIR, "Direction", s.gradient_dir)

        tbl.add_row(Text(""), Text(""))
        tbl.add_row(Text(" Effects", style="bold"), Text(""))

        for i, ename in enumerate(AVAILABLE_EFFECTS):
            fi = _F_EFX_BASE + i
            active = ename in s.active_effects
            mark = "[green]✓[/green]" if active else "[dim]○[/dim]"
            sel = s.current_field == fi
            arrow = "▶" if sel else " "
            lstyle = "bold reverse cyan" if sel else ""
            tbl.add_row(
                Text.from_markup(f"{arrow} {mark} {ename}", style=lstyle),
                Text(""),
            )

        tbl.add_row(Text(""), Text(""))
        row(_F_SPEED, "Speed", f"{s.effect_speed:.1f}")
        row(_F_AMP, "Amplitude", f"{s.effect_amplitude:.1f}")

        if s.status:
            tbl.add_row(Text(""), Text(s.status, style="yellow"))

        tbl.add_row(Text(""), Text(""))
        tbl.add_row(Text(" [s] save preset", style="dim"), Text(""))

        return tbl

    def _preview(self) -> Text:
        s = self._state
        try:
            banner = self._engine.render(s.text or "BANGEN", s.font)
            gradient = Gradient.from_string(s.gradient_str, direction=s.gradient_dir)
            banner.set_gradient(gradient)
            cfg = EffectConfig(speed=s.effect_speed, amplitude=s.effect_amplitude)
            for ename in s.active_effects:
                try:
                    banner.apply(build_effect(ename, config=cfg))
                except Exception:
                    pass
            return banner.render_frame(s.t)
        except Exception as exc:
            return Text(f"Preview error: {exc}", style="red")

    @staticmethod
    def _help_line() -> Text:
        h = Text()
        pairs = [
            ("↑↓", "navigate"),
            ("←→", "adjust"),
            ("Enter", "edit/toggle"),
            ("q", "quit"),
        ]
        for k, v in pairs:
            h.append(k, style="bold cyan")
            h.append(f" {v}  ", style="dim")
        return h
