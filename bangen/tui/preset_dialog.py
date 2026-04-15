"""Interactive modal dialog for loading presets (saved or from a file)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bangen.presets.manager import Preset, PresetManager


@dataclass(slots=True)
class _PresetInfo:
    name: str
    font: str
    gradient: str
    gradient_direction: str
    effects: tuple[str, ...]


class PresetDialog:
    """Modal for selecting a saved preset or loading from a JSON file."""

    def __init__(
        self,
        preset_manager: PresetManager,
        *,
        on_load: Callable[[Preset], None],
    ) -> None:
        self._pm = preset_manager
        self._on_load = on_load

        self.source = "saved"  # "saved" | "file"
        self.path = "preset.json"

        self._preset_names: list[str] = []
        self._preset_index = 0
        self._refresh_presets(initial=True)

        self.current_field = 0
        self.edit_field: str | None = None
        self.edit_buffer = ""
        self.edit_cursor = 0
        self.closed = False
        self.status_message = ""
        self.error_message = ""

    # ExportDialog compatibility hook.
    def sync(self) -> None:
        self._refresh_presets(initial=False)

    def render(self):
        self.sync()

        body = Table.grid(padding=(0, 1), expand=False)
        body.add_column(style="bold cyan", justify="right", width=12)
        body.add_column(width=48)

        body.add_row("Source", self._field_value("source", self._source_label()))

        if self.source == "saved":
            body.add_row("Preset", self._field_value("preset", self._preset_label()))
            info = self._selected_info()
            if info is not None:
                body.add_row("", Text(f"font: {info.font}", style="dim"))
                body.add_row(
                    "",
                    Text(
                        f"gradient: {info.gradient} ({info.gradient_direction})",
                        style="dim",
                    ),
                )
                effects = ", ".join(info.effects) if info.effects else "none"
                body.add_row("", Text(f"effects: {effects}", style="dim"))
        else:
            body.add_row("Path", self._field_value("path", self.path))

        body.add_row("Load", self._field_value("load", "Load preset", action=True))
        body.add_row("Cancel", self._field_value("cancel", "Close dialog", action=True))

        footer: list[RenderableType] = [body]

        if self.error_message:
            footer.append(Text(self.error_message, style="bold red"))

        footer.append(self._help_text())

        return Align.center(
            Panel(
                Group(*footer),
                title="[bold cyan]Presets[/bold cyan]",
                subtitle="[dim]Modal input active[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                width=72,
            ),
            vertical="middle",
        )

    def handle_input(self, key: str) -> None:
        self.sync()

        if self.edit_field is not None:
            self._handle_edit_input(key)
            return

        if key == "\x1b":
            self.closed = True
            return

        if key == "\x1b[A":
            self._move(-1)
            return

        if key == "\x1b[B":
            self._move(+1)
            return

        if key == "\x1b[D":
            self._nudge(-1)
            return

        if key == "\x1b[C":
            self._nudge(+1)
            return

        if key in ("\r", "\n"):
            self._activate()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _refresh_presets(self, *, initial: bool) -> None:
        names = sorted(self._pm.list_presets().keys())
        if initial or names != self._preset_names:
            selected_name = None
            if self._preset_names and 0 <= self._preset_index < len(self._preset_names):
                selected_name = self._preset_names[self._preset_index]
            self._preset_names = names
            if selected_name and selected_name in self._preset_names:
                self._preset_index = self._preset_names.index(selected_name)
            else:
                self._preset_index = 0

    def _active_fields(self) -> list[str]:
        fields = ["source"]
        if self.source == "saved":
            fields.append("preset")
        else:
            fields.append("path")
        fields.extend(["load", "cancel"])
        return fields

    def _current_field_id(self) -> str:
        fields = self._active_fields()
        if not fields:
            return ""
        self.current_field = max(0, min(self.current_field, len(fields) - 1))
        return fields[self.current_field]

    def _move(self, delta: int) -> None:
        fields = self._active_fields()
        if not fields:
            return
        self.current_field = (self.current_field + delta) % len(fields)

    def _nudge(self, delta: int) -> None:
        field = self._current_field_id()
        if field == "source":
            self._cycle_source(delta)
            return
        if field == "preset" and self.source == "saved":
            self._cycle_preset(delta)

    def _activate(self) -> None:
        field = self._current_field_id()
        self.error_message = ""

        if field == "source":
            self._cycle_source(+1)
            return

        if field == "preset" and self.source == "saved":
            self._cycle_preset(+1)
            return

        if field == "path" and self.source == "file":
            self.edit_field = "path"
            self.edit_buffer = self.path
            self.edit_cursor = len(self.edit_buffer)
            return

        if field == "load":
            self._load_selected()
            return

        if field == "cancel":
            self.closed = True

    def _load_selected(self) -> None:
        try:
            if self.source == "saved":
                preset = self._selected_preset()
                if preset is None:
                    raise ValueError("No presets available.")
            else:
                preset = self._pm.load_file(Path(self.path))

            self._on_load(preset)
            self.status_message = f"Loaded preset '{preset.name}'"
            self.closed = True
        except Exception as exc:
            self.error_message = str(exc)

    def _cycle_source(self, delta: int) -> None:
        sources = ["saved", "file"]
        idx = sources.index(self.source)
        self.source = sources[(idx + delta) % len(sources)]
        self.current_field = 0
        self.edit_field = None
        self.edit_buffer = ""
        self.error_message = ""

    def _cycle_preset(self, delta: int) -> None:
        if not self._preset_names:
            return
        self._preset_index = (self._preset_index + delta) % len(self._preset_names)

    def _selected_preset(self) -> Preset | None:
        if not self._preset_names:
            return None
        name = self._preset_names[self._preset_index]
        return self._pm.get(name)

    def _selected_info(self) -> _PresetInfo | None:
        preset = self._selected_preset()
        if preset is None:
            return None
        return _PresetInfo(
            name=preset.name,
            font=preset.font,
            gradient=preset.gradient,
            gradient_direction=preset.gradient_direction,
            effects=tuple(preset.effects),
        )

    def _source_label(self) -> str:
        return "< SAVED >" if self.source == "saved" else "< FILE >"

    def _preset_label(self) -> str:
        if not self._preset_names:
            return "(none found)"
        return f"< {self._preset_names[self._preset_index]} >"

    def _field_value(self, field_id: str, value: str, *, action: bool = False) -> Text:
        editing = self.edit_field == field_id
        selected = self._current_field_id() == field_id and self.edit_field is None

        if editing:
            # Show cursor position in edit buffer
            before_cursor = self.edit_buffer[: self.edit_cursor]
            after_cursor = self.edit_buffer[self.edit_cursor :]
            display = f"{before_cursor}█{after_cursor}"
        else:
            display = value
        style = "bold black on cyan" if (selected or editing) else "white"

        text = Text()
        text.append("▶ " if selected or editing else "  ", style="cyan")
        del action
        text.append(display, style=style)
        return text

    def _handle_edit_input(self, key: str) -> None:
        if key in ("\r", "\n"):
            self._commit_edit()
            return

        if key == "\x1b":
            self.edit_field = None
            self.edit_buffer = ""
            self.edit_cursor = 0
            self.error_message = ""
            return

        # Arrow key handling for cursor movement
        if key == "\x1b[D":  # Left arrow
            self.edit_cursor = max(0, self.edit_cursor - 1)
            return

        if key == "\x1b[C":  # Right arrow
            self.edit_cursor = min(len(self.edit_buffer), self.edit_cursor + 1)
            return

        if key in ("\x08", "\x7f"):  # Backspace
            if self.edit_cursor > 0:
                self.edit_buffer = (
                    self.edit_buffer[: self.edit_cursor - 1]
                    + self.edit_buffer[self.edit_cursor :]
                )
                self.edit_cursor -= 1
            return

        if key == "\x16":  # Ctrl+V for paste
            try:
                import pyperclip

                clipboard_text = pyperclip.paste()
                self.edit_buffer = (
                    self.edit_buffer[: self.edit_cursor]
                    + clipboard_text
                    + self.edit_buffer[self.edit_cursor :]
                )
                self.edit_cursor += len(clipboard_text)
            except Exception:
                pass  # Silently ignore if pyperclip not available
            return

        if key.isprintable():
            self.edit_buffer = (
                self.edit_buffer[: self.edit_cursor]
                + key
                + self.edit_buffer[self.edit_cursor :]
            )
            self.edit_cursor += 1

    def _commit_edit(self) -> None:
        value = self.edit_buffer.strip()
        self.edit_field = None
        self.edit_buffer = ""
        self.error_message = ""
        if value:
            self.path = value

    def _help_text(self) -> Text:
        help_text = Text()
        help_text.append("↑↓", style="bold cyan")
        help_text.append(" move  ", style="dim")
        help_text.append("←→", style="bold cyan")
        help_text.append(" toggle  ", style="dim")
        help_text.append("Enter", style="bold cyan")
        help_text.append(" edit/load  ", style="dim")
        help_text.append("Esc", style="bold cyan")
        help_text.append(" cancel", style="dim")
        return help_text
