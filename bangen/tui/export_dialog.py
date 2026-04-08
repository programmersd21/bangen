"""Interactive modal export dialog."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from threading import Thread

from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from bangen.export.exporter import Exporter
from bangen.export.gif import MAX_GIF_FRAMES

_FORMATS = ("gif", "png", "txt")


class ExportDialog:
    def __init__(self, banner, engine):
        self.banner = deepcopy(banner)
        self.engine = engine
        self.exporter = Exporter()

        self.format = "gif"
        self.path = "banner.gif"
        self.duration = 3.0
        self.fps = 20

        self.current_field = 0
        self.edit_field: str | None = None
        self.edit_buffer = ""
        self.loading = False
        self.closed = False
        self.status_message = ""
        self.error_message = ""
        self.warning_message = ""
        self.confirm_overwrite = False

        self._worker: Thread | None = None
        self._worker_error: str | None = None
        self._worker_result: str | None = None

    def render(self):
        self.sync()

        body = Table.grid(padding=(0, 1), expand=False)
        body.add_column(style="bold cyan", justify="right", width=12)
        body.add_column(width=42)

        body.add_row("Format", self._field_value("format", self._format_label()))
        body.add_row("Path", self._field_value("path", self.path))

        if self.format == "gif":
            body.add_row("Duration", self._field_value("duration", f"{self.duration:.2f}"))
            body.add_row("FPS", self._field_value("fps", str(self.fps)))
            body.add_row("Frames", self._gif_frame_summary())

        body.add_row("Export", self._field_value("export", "Start export", action=True))
        body.add_row("Cancel", self._field_value("cancel", "Close dialog", action=True))

        footer: list[object] = [body]

        if self.loading and self.format == "gif":
            footer.append(Spinner("dots", text="Rendering GIF frames..."))

        if self.warning_message:
            footer.append(Text(self.warning_message, style="bold yellow"))

        if self.error_message:
            footer.append(Text(self.error_message, style="bold red"))

        footer.append(self._help_text())

        return Align.center(
            Panel(
                Group(*footer),
                title="[bold cyan]Export[/bold cyan]",
                subtitle="[dim]Modal input active[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
                width=64,
            ),
            vertical="middle",
        )

    def handle_input(self, key):
        self.sync()

        if self.loading:
            return

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
            self._move(1)
            return

        if key == "\x1b[C" and self._current_field_id() == "format":
            self._cycle_format(+1)
            return

        if key == "\x1b[D" and self._current_field_id() == "format":
            self._cycle_format(-1)
            return

        if key in ("\r", "\n"):
            self._activate_current_field()

    def export(self):
        self.sync()
        if self.loading:
            return

        self.error_message = ""
        self.warning_message = ""

        try:
            target = self._target_path()
            if target.exists() and not self.confirm_overwrite:
                self.confirm_overwrite = True
                self.warning_message = (
                    f"{target.name} already exists. Press Enter again to overwrite."
                )
                return
            self.confirm_overwrite = False

            if self.format == "gif":
                self.loading = True
                self._worker_error = None
                self._worker_result = None
                self._worker = Thread(
                    target=self._run_gif_export,
                    args=(target,),
                    daemon=True,
                )
                self._worker.start()
                return

            if self.format == "png":
                self.exporter.export_png(self.banner, target)
            else:
                self.exporter.export_txt(self.banner, target)
            self.status_message = f"✓ Exported to {target}"
            self.closed = True
        except Exception as exc:
            self.error_message = str(exc)

    def _run_gif_export(self, target: Path) -> None:
        try:
            self.exporter.export_gif(
                self.banner,
                target,
                duration=self.duration,
                fps=self.fps,
            )
            self._worker_result = str(target)
        except Exception as exc:
            self._worker_error = str(exc)

    def sync(self) -> None:
        worker = self._worker
        if worker is None or worker.is_alive():
            return

        worker.join(timeout=0)
        self._worker = None
        self.loading = False

        if self._worker_error is not None:
            self.error_message = self._worker_error
            self._worker_error = None
            return

        if self._worker_result is not None:
            self.status_message = f"✓ Exported to {self._worker_result}"
            self._worker_result = None
            self.closed = True

    def _move(self, delta: int) -> None:
        fields = self._active_fields()
        self.current_field = (self.current_field + delta) % len(fields)
        self.warning_message = ""
        self.confirm_overwrite = False

    def _activate_current_field(self) -> None:
        field_id = self._current_field_id()

        if field_id == "format":
            self._cycle_format(+1)
            return

        if field_id in {"path", "duration", "fps"}:
            self.edit_field = field_id
            self.edit_buffer = self._editable_value(field_id)
            self.confirm_overwrite = False
            return

        if field_id == "export":
            self.export()
            return

        self.closed = True

    def _handle_edit_input(self, key: str) -> None:
        if key in ("\r", "\n"):
            self._commit_edit()
            return

        if key == "\x1b":
            self.edit_field = None
            self.edit_buffer = ""
            return

        if key in ("\x08", "\x7f"):
            self.edit_buffer = self.edit_buffer[:-1]
            return

        if key.isprintable():
            if self.edit_field == "path":
                self.edit_buffer += key
                return
            if key.isdigit() or key == ".":
                self.edit_buffer += key

    def _commit_edit(self) -> None:
        field_id = self.edit_field
        value = self.edit_buffer.strip()
        self.edit_field = None
        self.edit_buffer = ""
        self.warning_message = ""
        self.error_message = ""
        self.confirm_overwrite = False

        try:
            if field_id == "path":
                self.path = self._apply_extension(value or self.path)
                return

            if field_id == "duration":
                parsed = float(value)
                if parsed <= 0:
                    raise ValueError("Duration must be greater than 0.")
                self.duration = parsed
                return

            if field_id == "fps":
                parsed = int(float(value))
                if parsed <= 0:
                    raise ValueError("FPS must be greater than 0.")
                self.fps = parsed
        except ValueError as exc:
            self.error_message = str(exc)

    def _cycle_format(self, delta: int) -> None:
        current_index = _FORMATS.index(self.format)
        self.format = _FORMATS[(current_index + delta) % len(_FORMATS)]
        self.path = self._apply_extension(self.path)
        self.warning_message = ""
        self.error_message = ""
        self.confirm_overwrite = False

        fields = self._active_fields()
        if self.current_field >= len(fields):
            self.current_field = len(fields) - 1

    def _current_field_id(self) -> str:
        return self._active_fields()[self.current_field]

    def _active_fields(self) -> list[str]:
        fields = ["format", "path"]
        if self.format == "gif":
            fields.extend(["duration", "fps"])
        fields.extend(["export", "cancel"])
        return fields

    def _editable_value(self, field_id: str) -> str:
        if field_id == "path":
            return self.path
        if field_id == "duration":
            return f"{self.duration:.2f}"
        if field_id == "fps":
            return str(self.fps)
        return ""

    def _field_value(self, field_id: str, value: str, *, action: bool = False) -> Text:
        editing = self.edit_field == field_id
        selected = self._current_field_id() == field_id and self.edit_field is None

        display = f"{self.edit_buffer}█" if editing else value
        style = "bold black on cyan" if (selected or editing) else "white"

        text = Text()
        text.append("▶ " if selected or editing else "  ", style="cyan")
        if action:
            text.append(display, style=style)
        else:
            text.append(display, style=style)
        return text

    def _format_label(self) -> str:
        return f"< {self.format.upper()} >"

    def _gif_frame_summary(self) -> Text:
        requested_frames = max(1, round(self.duration * self.fps))
        frame_text = str(min(requested_frames, MAX_GIF_FRAMES))
        if requested_frames > MAX_GIF_FRAMES:
            return Text(f"{frame_text} (capped)", style="yellow")
        return Text(frame_text, style="white")

    def _help_text(self) -> Text:
        help_text = Text()
        help_text.append("↑↓", style="bold cyan")
        help_text.append(" move  ", style="dim")
        help_text.append("←→", style="bold cyan")
        help_text.append(" toggle format  ", style="dim")
        help_text.append("Enter", style="bold cyan")
        help_text.append(" edit/export  ", style="dim")
        help_text.append("Esc", style="bold cyan")
        help_text.append(" cancel", style="dim")
        return help_text

    def _target_path(self) -> Path:
        target = Path(self._apply_extension(self.path)).expanduser()
        if target.name in {"", ".", ".."}:
            raise ValueError("Export path cannot be empty.")
        if target.exists() and target.is_dir():
            raise ValueError(f"Export path points to a directory: {target}")
        return target

    def _apply_extension(self, raw_path: str) -> str:
        cleaned = raw_path.strip() or f"banner.{self.format}"
        target = Path(cleaned)
        expected_suffix = f".{self.format}"
        if target.suffix.lower() != expected_suffix:
            target = target.with_suffix(expected_suffix)
        return str(target)
