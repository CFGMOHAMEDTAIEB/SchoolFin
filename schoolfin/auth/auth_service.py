from __future__ import annotations

from typing import Optional

from schoolfin.auth.session import Session
from schoolfin.db.db import connect, sha256


def authenticate(username: str, password: str, role: str | None = None) -> Optional[Session]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, password_hash FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None
    if row["password_hash"] != sha256(password):
        return None
    if role and row["role"] != role:
        return None

    return Session(user_id=row["id"], username=row["username"], role=row["role"])

