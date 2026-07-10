from __future__ import annotations

from pathlib import Path


def get_app_icon_path() -> Path | None:
    base_dir = Path(__file__).resolve().parents[1]
    candidate = base_dir / "assets" / "schoolfin_icon.svg"
    return candidate if candidate.exists() else None
