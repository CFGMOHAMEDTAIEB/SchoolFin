from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _exe_dir() -> Path:
    # For packaged apps
    if getattr(__import__("sys"), "frozen", False):
        import sys

        return Path(sys.executable).resolve().parent
    # For dev
    return Path(__file__).resolve().parents[2]


def _default_data_dir(app_name: str = "SchoolFin") -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / app_name
    return Path.home() / ".local" / "share" / app_name


def _legacy_db_candidates(filename: str = "schoolfin.sqlite") -> list[Path]:
    candidates = [
        _exe_dir() / filename,
        Path(__file__).resolve().parents[2] / filename,
    ]
    # unique paths while preserving order
    unique: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def app_db_path(filename: str = "schoolfin.sqlite") -> Path:
    override = os.environ.get("SCHOOLFIN_DB_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _default_data_dir() / filename


def _migrate_legacy_db_if_needed(filename: str = "schoolfin.sqlite") -> None:
    target = app_db_path(filename)
    if target.exists():
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    for legacy in _legacy_db_candidates(filename):
        if legacy.exists() and legacy.resolve() != target.resolve():
            shutil.copy2(legacy, target)
            break


def _ensure_payment_history_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(payment_history)")
    columns = {row[1]: row for row in cur.fetchall()}

    # Add snapshot columns for backward compatibility if missing.
    if "student_name_snapshot" not in columns:
        cur.execute("ALTER TABLE payment_history ADD COLUMN student_name_snapshot TEXT")
    if "class_name_snapshot" not in columns:
        cur.execute("ALTER TABLE payment_history ADD COLUMN class_name_snapshot TEXT")

    cur.execute("PRAGMA table_info(payment_history)")
    columns = {row[1]: row for row in cur.fetchall()}
    student_col = columns.get("student_id")
    student_not_null = bool(student_col and student_col[3] == 1)

    cur.execute("PRAGMA foreign_key_list(payment_history)")
    fk_rows = cur.fetchall()
    student_fk_wrong = False
    for fk in fk_rows:
        # pragma columns: id, seq, table, from, to, on_update, on_delete, match
        if fk[3] == "student_id" and str(fk[6]).upper() != "SET NULL":
            student_fk_wrong = True
            break

    needs_rebuild = student_not_null or student_fk_wrong
    if not needs_rebuild:
        conn.commit()
        return

    cur.execute("PRAGMA foreign_keys = OFF")
    cur.execute("BEGIN")
    try:
        cur.execute("ALTER TABLE payment_history RENAME TO payment_history_old")
        cur.execute(
            """
            CREATE TABLE payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER,
                student_id INTEGER,
                student_name_snapshot TEXT,
                class_name_snapshot TEXT,
                action TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                old_amount REAL,
                new_amount REAL,
                old_paid_date TEXT,
                new_paid_date TEXT,
                changed_by INTEGER NOT NULL,
                changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                note TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL,
                FOREIGN KEY(changed_by) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE SET NULL
            )
            """
        )
        cur.execute(
            """
            INSERT INTO payment_history (
                id,
                payment_id,
                student_id,
                student_name_snapshot,
                class_name_snapshot,
                action,
                old_status,
                new_status,
                old_amount,
                new_amount,
                old_paid_date,
                new_paid_date,
                changed_by,
                changed_at,
                note
            )
            SELECT
                h.id,
                h.payment_id,
                h.student_id,
                COALESCE(h.student_name_snapshot, s.full_name),
                COALESCE(h.class_name_snapshot, c.name),
                h.action,
                h.old_status,
                h.new_status,
                h.old_amount,
                h.new_amount,
                h.old_paid_date,
                h.new_paid_date,
                h.changed_by,
                h.changed_at,
                h.note
            FROM payment_history_old h
            LEFT JOIN students s ON s.id = h.student_id
            LEFT JOIN classes c ON c.id = s.class_id
            """
        )
        cur.execute("DROP TABLE payment_history_old")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_student ON payment_history(student_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_changed_by ON payment_history(changed_by)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.execute("PRAGMA foreign_keys = ON")


def connect() -> sqlite3.Connection:
    db_file = app_db_path()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _ensure_student_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(students)")
    columns = {row[1]: row for row in cur.fetchall()}

    schema_updates = {
        "payment_frequency": "TEXT NOT NULL DEFAULT 'monthly'",
        "address": "TEXT",
        "birth_date": "TEXT",
        "parent_name": "TEXT",
        "parent_phone": "TEXT",
        "notes": "TEXT",
        "payment_method": "TEXT",
    }

    for column_name, definition in schema_updates.items():
        if column_name not in columns:
            cur.execute(f"ALTER TABLE students ADD COLUMN {column_name} {definition}")
    conn.commit()


def init_db() -> None:
    _migrate_legacy_db_if_needed()
    conn = connect()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','financial')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            payment_frequency TEXT NOT NULL DEFAULT 'monthly',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE
        );

        -- A payment record represents the state for a student (paid/unpaid) for a specific payment date.
        -- If you want periods (month/term), you can add 'period' later.
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            paid_date TEXT,
            status TEXT NOT NULL CHECK(status IN ('paid','unpaid')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            created_by INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        );

        -- audit log for changes (who changed the payment, and what changed)
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER,
            student_id INTEGER,
            student_name_snapshot TEXT,
            class_name_snapshot TEXT,
            action TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            old_amount REAL,
            new_amount REAL,
            old_paid_date TEXT,
            new_paid_date TEXT,
            changed_by INTEGER NOT NULL,
            changed_at TEXT NOT NULL DEFAULT (datetime('now')),
            note TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL,
            FOREIGN KEY(changed_by) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);
        CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);
        CREATE INDEX IF NOT EXISTS idx_history_student ON payment_history(student_id);
        CREATE INDEX IF NOT EXISTS idx_history_changed_by ON payment_history(changed_by);
        """
    )

    _ensure_student_schema(conn)
    _ensure_payment_history_schema(conn)

    # Seed default users if empty
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        # default passwords
        default = [
            ("admin", "admin123", "admin"),
            ("financial", "financial123", "financial"),
        ]
        cur.executemany(
            "INSERT INTO users(username, password_hash, role) VALUES (?,?,?)",
            [(u, sha256(pw), role) for (u, pw, role) in default],
        )

    conn.commit()
    conn.close()

