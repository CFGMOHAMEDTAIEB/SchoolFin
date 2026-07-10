from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "SchoolFin"
    # DB path: stored in same folder as the exe when packaged; otherwise in project root.
    @property
    def db_path(self) -> str:
        # In PyInstaller, sys._MEIPASS points to temp; better to use exe directory.
        # We'll override in db layer using the actual executable directory.
        return ""  # resolved elsewhere


SETTINGS = Settings()

