from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    user_id: int
    username: str
    role: str  # admin | financial


_global_session: Optional[Session] = None


def set_session(s: Optional[Session]) -> None:
    global _global_session
    _global_session = s


def get_session() -> Optional[Session]:
    return _global_session

