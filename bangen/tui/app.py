"""Full-screen interactive TUI with split controls/preview layout."""

from __future__ import annotations

import sys
import time
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from typing import Any, Callable

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bangen.effects import AVAILABLE_EFFECTS, EFFECT_TIERS, EffectConfig, build_effect
from bangen.gradients.gradient import Gradient
from bangen.presets.manager import Preset, PresetManager
from bangen.rendering.engine import PRESET_FONTS, RenderEngine
from bangen.rendering.sizing import calculate_auto_size, format_size_info
from bangen.tui.export_dialog import ExportDialog
from bangen.tui.preset_dialog import PresetDialog

# field indices
_F_TEXT = 0
_F_FONT = 1
_F_GRAD = 2
_F_DIR = 3
_F_EFX_BASE = 4
_F_SPEED = _F_EFX_BASE + len(AVAILABLE_EFFECTS)
_F_AMP = _F_SPEED + 1
_NUM_FIELDS = _F_AMP + 1
_EFFECT_WINDOW = 10


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
    show_size_info: bool = False
    size_info: str = ""
    show_changelog: bool = False
    changelog_content: str = ""
    changelog_scroll_pos: int = 0


class TUIApp:
    """Keyboard-driven live TUI banner designer."""

    def __init__(self, engine: RenderEngine, preset_manager: PresetManager) -> None:
        self.engine = engine
        self._pm = preset_manager
        self._state = TUIState()
        self._console = Console()
        self.banner = None
        self.active_modal: ExportDialog | PresetDialog | None = None

    def load_preset(self, preset: Preset) -> None:
        state = self._state
        state.font = preset.font
        try:
            state.font_idx = PRESET_FONTS.index(preset.font)
        except ValueError:
            state.font_idx = 0
        state.gradient_str = preset.gradient
        state.gradient_dir = preset.gradient_direction
        state.active_effects = list(preset.effects)

    def set_text(self, text: str) -> None:
        self._state.text = text

    def open_export_dialog(self):
        self.banner = self._compose_banner()
        self.active_modal = ExportDialog(self.banner, self.engine)

    def run(self) -> TUIState:
        if sys.platform == "win32":
            self._run_windows()
        else:
            self._run_unix()
        return self._state

    def _run_unix(self) -> None:
        import termios
        import tty

        fd = sys.stdin.fileno()
        termios_mod: Any = termios
        tty_mod: Any = tty
        saved = termios_mod.tcgetattr(fd)
        try:
            tty_mod.setraw(fd)
            self._event_loop(lambda: self._unix_key(fd))
        finally:
            termios_mod.tcsetattr(fd, termios_mod.TCSADRAIN, saved)

    def _unix_key(self, fd: int) -> str | None:
        import select

        ready, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not ready:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            import select as sel

            ready2, _, _ = sel.select([sys.stdin], [], [], 0.05)
            if ready2:
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ready3, _, _ = sel.select([sys.stdin], [], [], 0.05)
                    if ready3:
                        ch3 = sys.stdin.read(1)
                        return f"\x1b[{ch3}"
        return ch

    def _run_windows(self) -> None:
        import msvcrt

        key_map = {b"H": "\x1b[A", b"P": "\x1b[B", b"K": "\x1b[D", b"M": "\x1b[C"}

        def read() -> str | None:
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                return key_map.get(msvcrt.getch(), "")
            try:
                return ch.decode("utf-8")
            except Exception:
                return None

        self._event_loop(read)

    def _event_loop(self, read_key: Callable[[], str | None]) -> None:
        state = self._state
        start = time.monotonic()

        with Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=20,
            screen=True,
        ) as live:
            while state.running:
                state.t = time.monotonic() - start
                self._sync_modal()
                live.update(self._build_layout())
                key = read_key()
                if key:
                    self._handle(key)
                time.sleep(0.05)

    def _handle(self, key: str) -> None:
        if self.active_modal is not None:
            self.active_modal.handle_input(key)
            self._sync_modal()
            return

        if self._state.editing:
            self._handle_edit(key)
            return

        self._handle_nav(key)

    def _handle_nav(self, key: str) -> None:
        state = self._state

        if state.show_changelog:
            if key == "\x1b[A":  # Up
                state.changelog_scroll_pos = max(0, state.changelog_scroll_pos - 1)
            elif key == "\x1b[B":  # Down
                state.changelog_scroll_pos += 1
            elif key in ("c", "C"):
                state.show_changelog = False
            return

        if key == "\x1b[A":
            state.current_field = (state.current_field - 1) % _NUM_FIELDS
        elif key == "\x1b[B":
            state.current_field = (state.current_field + 1) % _NUM_FIELDS
        elif key in ("\r", "\n"):
            self._activate()
        elif key == "\x1b[C":
            self._nudge(+1)
        elif key == "\x1b[D":
            self._nudge(-1)
        elif key in ("c", "C"):
            if not state.changelog_content:
                try:
                    with urllib.request.urlopen(
                        "https://raw.githubusercontent.com/programmersd21/bangen/refs/heads/main/CHANGELOG.md"
                    ) as response:
                        content = response.read().decode("utf-8")
                        lines = content.splitlines()
                        if lines and lines[0].strip() == "# Changelog":
                            content = "\n".join(lines[1:]).strip()
                        state.changelog_content = content
                        state.changelog_scroll_pos = 0
                except Exception as exc:
                    state.status = f"Changelog error: {exc}"
            if state.changelog_content:
                state.show_changelog = not state.show_changelog
        elif key in ("i", "I"):
            webbrowser.open("https://github.com/programmersd21/bangen/issues/new")
            state.status = "Opened issues page in browser"
        elif key in ("e", "E"):
            try:
                self.open_export_dialog()
            except Exception as exc:
                state.status = f"Export unavailable: {exc}"
        elif key in ("l", "L"):
            try:
                self.active_modal = PresetDialog(self._pm, on_load=self.load_preset)
            except Exception as exc:
                state.status = f"Preset loader unavailable: {exc}"
        elif key in ("a", "A"):
            state.show_size_info = not state.show_size_info
            if state.show_size_info:
                state.status = "Auto-size info: ON"
            else:
                state.status = "Auto-size info: OFF"
        elif key in ("q", "Q", "\x03", "\x04"):
            state.running = False
        elif key in ("s", "S"):
            self._quick_save()

    def _handle_edit(self, key: str) -> None:
        state = self._state

        if key in ("\r", "\n"):
            field = state.current_field
            if field == _F_TEXT:
                state.text = state.edit_buffer or state.text
            elif field == _F_GRAD:
                state.gradient_str = state.edit_buffer or state.gradient_str
            state.editing = False
            state.edit_buffer = ""
        elif key == "\x1b":
            state.editing = False
            state.edit_buffer = ""
        elif key in ("\x7f", "\x08"):
            state.edit_buffer = state.edit_buffer[:-1]
        elif key == "\x16":  # Ctrl+V for paste
            try:
                import pyperclip

                clipboard_text = pyperclip.paste()
                state.edit_buffer += clipboard_text
            except Exception:
                pass  # Silently ignore if pyperclip not available
        elif key.isprintable():
            state.edit_buffer += key

    def _activate(self) -> None:
        state = self._state
        field = state.current_field

        if field == _F_TEXT:
            state.editing = True
            state.edit_buffer = state.text
        elif field == _F_FONT:
            state.font_idx = (state.font_idx + 1) % len(PRESET_FONTS)
            state.font = PRESET_FONTS[state.font_idx]
        elif field == _F_GRAD:
            state.editing = True
            state.edit_buffer = state.gradient_str
        elif field == _F_DIR:
            state.gradient_dir = (
                "vertical" if state.gradient_dir == "horizontal" else "horizontal"
            )
        elif _F_EFX_BASE <= field < _F_SPEED:
            effect_name = AVAILABLE_EFFECTS[field - _F_EFX_BASE]
            if effect_name in state.active_effects:
                state.active_effects.remove(effect_name)
            else:
                state.active_effects.append(effect_name)

    def _nudge(self, delta: int) -> None:
        state = self._state
        field = state.current_field

        if field == _F_FONT:
            state.font_idx = (state.font_idx + delta) % len(PRESET_FONTS)
            state.font = PRESET_FONTS[state.font_idx]
        elif field == _F_SPEED:
            state.effect_speed = round(max(0.1, state.effect_speed + delta * 0.1), 2)
        elif field == _F_AMP:
            state.effect_amplitude = round(
                max(0.1, state.effect_amplitude + delta * 0.1),
                2,
            )

    def _quick_save(self) -> None:
        state = self._state
        name = f"tui_{int(time.time())}"
        self._pm.save(
            Preset(
                name=name,
                font=state.font,
                gradient=state.gradient_str,
                gradient_direction=state.gradient_dir,
                effects=list(state.active_effects),
                effect_config={},
            )
        )
        state.status = f"Saved as '{name}'"

    def _build_layout(self):
        if self.active_modal is not None:
            return self.active_modal.render()
        if self._state.show_changelog:
            lines = self._state.changelog_content.splitlines()
            display_lines = lines[self._state.changelog_scroll_pos :]
            return Panel(
                Markdown("\n".join(display_lines)),
                title="[bold cyan]Changelog[/bold cyan]",
                subtitle="[dim]↑↓ to scroll, 'c' to close[/dim]",
                box=box.ROUNDED,
            )
        return self._build_main_layout()

    def _build_main_layout(self) -> Layout:
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
        state = self._state
        table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        table.add_column("k", no_wrap=True, width=18)
        table.add_column("v")

        def row(field_index: int, label: str, value: str) -> None:
            selected = state.current_field == field_index
            arrow = "▶" if selected else " "
            label_style = "bold reverse cyan" if selected else "dim"
            value_style = "bold cyan" if selected else "white"
            table.add_row(
                Text(f"{arrow} {label}", style=label_style),
                Text(value, style=value_style),
            )

        text_value = (
            f"{state.edit_buffer}█"
            if state.editing and state.current_field == _F_TEXT
            else state.text
        )
        row(_F_TEXT, "Text", text_value)
        row(_F_FONT, "Font", state.font)

        gradient_value = (
            f"{state.edit_buffer}█"
            if state.editing and state.current_field == _F_GRAD
            else state.gradient_str
        )
        row(_F_GRAD, "Gradient", gradient_value)
        row(_F_DIR, "Direction", state.gradient_dir)

        table.add_row(Text(""), Text(""))
        table.add_row(
            Text(" Effects", style="bold"),
            Text(self._effects_summary(), style="dim"),
        )

        start, end = self._effect_window_bounds()
        visible_effects = AVAILABLE_EFFECTS[start:end]
        visible_set = set(visible_effects)

        for tier_name, tier_effects in EFFECT_TIERS.items():
            tier_visible = [name for name in tier_effects if name in visible_set]
            if not tier_visible:
                continue
            table.add_row(
                Text(f" {tier_name.title()}", style="bold magenta"),
                Text(""),
            )
            for effect_name in tier_visible:
                index = AVAILABLE_EFFECTS.index(effect_name)
                field_index = _F_EFX_BASE + index
                active = effect_name in state.active_effects
                mark = "[green]✓[/green]" if active else "[dim]○[/dim]"
                selected = state.current_field == field_index
                arrow = "▶" if selected else " "
                label_style = "bold reverse cyan" if selected else ""
                pretty_name = effect_name.replace("_", " ")
                table.add_row(
                    Text.from_markup(
                        f"{arrow} {mark} {pretty_name}", style=label_style
                    ),
                    Text(""),
                )

        if start > 0 or end < len(AVAILABLE_EFFECTS):
            table.add_row(
                Text(" [effect list scrolls with selection]", style="dim"),
                Text(""),
            )

        table.add_row(Text(""), Text(""))
        row(_F_SPEED, "Speed", f"{state.effect_speed:.1f}")
        row(_F_AMP, "Amplitude", f"{state.effect_amplitude:.1f}")

        if state.status:
            table.add_row(Text(""), Text(state.status, style="yellow"))

        if state.show_size_info and state.size_info:
            table.add_row(Text(""), Text(state.size_info, style="cyan"))

        table.add_row(Text(""), Text(""))
        table.add_row(
            Text(
                " [l] load preset  [a] size info  [e] export  [s] save preset",
                style="dim",
            ),
            Text(""),
        )
        return table

    def _effects_summary(self) -> str:
        active = self._state.active_effects
        if not active:
            return "none"
        if len(active) <= 3:
            return ", ".join(name.replace("_", " ") for name in active)
        return f"{len(active)} enabled"

    def _effect_window_bounds(self) -> tuple[int, int]:
        current_index = self._state.current_field - _F_EFX_BASE
        if current_index < 0 or current_index >= len(AVAILABLE_EFFECTS):
            current_index = 0
        half = _EFFECT_WINDOW // 2
        start = max(0, current_index - half)
        end = min(len(AVAILABLE_EFFECTS), start + _EFFECT_WINDOW)
        start = max(0, end - _EFFECT_WINDOW)
        return start, end

    def _preview(self) -> Text:
        try:
            banner = self._compose_banner()
            self.banner = banner
            # Calculate size info if show_size_info is enabled
            if self._state.show_size_info:
                try:
                    size_config = calculate_auto_size(banner)
                    self._state.size_info = format_size_info(size_config, banner)
                except Exception:
                    self._state.size_info = ""
            return banner.render_frame(self._state.t)
        except Exception as exc:
            self.banner = None
            return Text(f"Preview error: {exc}", style="red")

    def _compose_banner(self):
        state = self._state
        banner = self.engine.render(state.text or "BANGEN", state.font)
        gradient = Gradient.from_string(
            state.gradient_str,
            direction=state.gradient_dir,
        )
        banner.set_gradient(gradient)

        config = EffectConfig(
            speed=state.effect_speed,
            amplitude=state.effect_amplitude,
        )
        for effect_name in state.active_effects:
            banner.apply(build_effect(effect_name, config=config))
        return banner

    def _sync_modal(self) -> None:
        if self.active_modal is None:
            return

        self.active_modal.sync()
        if self.active_modal.closed:
            if self.active_modal.status_message:
                self._state.status = self.active_modal.status_message
            self.active_modal = None

    @staticmethod
    def _help_line() -> Text:
        help_text = Text()
        pairs = [
            ("↑↓", "navigate"),
            ("←→", "adjust"),
            ("Enter", "edit/toggle"),
            ("c", "changelog"),
            ("i", "report issue"),
            ("l", "load presets"),
            ("a", "size info"),
            ("e", "export"),
            ("q", "quit"),
        ]
        for key, value in pairs:
            help_text.append(key, style="bold cyan")
            help_text.append(f" {value}  ", style="dim")
        return help_text
