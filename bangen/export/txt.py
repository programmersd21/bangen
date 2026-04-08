"""Plain-text export helpers."""

from __future__ import annotations

from pathlib import Path


def export_txt(path: Path, banner: str) -> None:
    path.write_text(banner.rstrip("\n") + "\n", encoding="utf-8")
