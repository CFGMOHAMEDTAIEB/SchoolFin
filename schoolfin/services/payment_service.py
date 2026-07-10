from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from schoolfin.db.db import connect


_PAYMENT_FREQUENCIES = {
    "monthly": "Mensuel",
    "quarterly": "Trimestriel",
    "yearly": "Annuel",
}

DEFAULT_ANNUAL_FEE = 3600.0


def normalize_payment_frequency(value: Optional[str]) -> str:
    if not value:
        return "monthly"
    normalized = str(value).strip().lower()
    aliases = {
        "mensuel": "monthly",
        "mensuelle": "monthly",
        "monthly": "monthly",
        "trimestriel": "quarterly",
        "trimestrielle": "quarterly",
        "quarterly": "quarterly",
        "annuel": "yearly",
        "annuelle": "yearly",
        "yearly": "yearly",
    }
    return aliases.get(normalized, "monthly")


def format_payment_frequency(value: Optional[str]) -> str:
    return _PAYMENT_FREQUENCIES.get(normalize_payment_frequency(value), "Mensuel")


def compute_due_amount(payment_frequency: Optional[str], annual_fee: float = DEFAULT_ANNUAL_FEE) -> float:
    normalized_frequency = normalize_payment_frequency(payment_frequency)
    factor = {
        "monthly": 1 / 12,
        "quarterly": 1 / 4,
        "yearly": 1.0,
    }.get(normalized_frequency, 1 / 12)
    return round(float(annual_fee) * factor, 2)


def _get_latest_payment_by_student(conn: sqlite3.Connection, student_id: int) -> Optional[sqlite3.Row]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM payments
        WHERE student_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_id,),
    )
    return cur.fetchone()


def list_classes():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.id,
            c.name,
            COUNT(s.id) AS student_count
        FROM classes c
        LEFT JOIN students s ON s.class_id = c.id
        GROUP BY c.id, c.name
        ORDER BY c.name
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]



def list_students_by_class(class_id: Optional[int] = None):
    conn = connect()
    cur = conn.cursor()
    if class_id is None:
        cur.execute(
            """
            SELECT
                s.id,
                c.name AS class_name,
                s.full_name,
                s.phone,
                s.address,
                s.birth_date,
                s.parent_name,
                s.parent_phone,
                s.notes,
                s.payment_method,
                s.payment_frequency
            FROM students s JOIN classes c ON c.id = s.class_id
            ORDER BY c.name, s.full_name
            """
        )
    else:
        cur.execute(
            """
            SELECT
                s.id,
                c.name AS class_name,
                s.full_name,
                s.phone,
                s.address,
                s.birth_date,
                s.parent_name,
                s.parent_phone,
                s.notes,
                s.payment_method,
                s.payment_frequency
            FROM students s JOIN classes c ON c.id = s.class_id
            WHERE s.class_id = ?
            ORDER BY s.full_name
            """,
            (class_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_latest_payment(student_id: int) -> Optional[dict]:
    conn = connect()
    p = _get_latest_payment_by_student(conn, student_id)
    conn.close()
    return dict(p) if p else None


def set_payment_status(
    *,
    student_id: int,
    status: str,
    amount: float,
    paid_date: Optional[str],
    changed_by: int,
    note: str = "",
) -> int:
    if status not in ("paid", "unpaid"):
        raise ValueError("status must be paid or unpaid")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT s.full_name AS student_name, c.name AS class_name
        FROM students s
        JOIN classes c ON c.id = s.class_id
        WHERE s.id = ?
        """,
        (student_id,),
    )
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        raise ValueError("Student not found")

    old = _get_latest_payment_by_student(conn, student_id)

    old_status = old["status"] if old else None
    old_amount = old["amount"] if old else None
    old_paid_date = old["paid_date"] if old else None

    # If unpaid: keep amount = 0 and paid_date nullable unless you want history.
    final_amount = float(amount)
    final_paid_date = paid_date

    if status == "unpaid":
        final_amount = 0.0
        final_paid_date = None

    cur.execute(
        """
        INSERT INTO payments(student_id, amount, paid_date, status, created_by)
        VALUES (?,?,?,?,?)
        """,
        (student_id, final_amount, final_paid_date, status, changed_by),
    )
    payment_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO payment_history(
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
            note
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            payment_id,
            student_id,
            student_row["student_name"],
            student_row["class_name"],
            "set_status",
            old_status,
            status,
            old_amount,
            final_amount,
            old_paid_date,
            final_paid_date,
            changed_by,
            note,
        ),
    )

    conn.commit()
    conn.close()
    return int(payment_id)


def delete_class(class_id: int) -> None:
    """Delete a class.

    Note: students referencing this class are deleted automatically due to ON DELETE CASCADE.
    """
    conn = connect()
    conn.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()



def get_class(class_id: int) -> Optional[dict]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM classes WHERE id = ?", (class_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_class(class_id: int, name: str) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE classes SET name = ? WHERE id = ?", (name, class_id))
    if cur.rowcount == 0:
        conn.close()
        raise ValueError("Class not found")
    conn.commit()
    conn.close()


def create_class(name: str) -> int:
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO classes(name) VALUES (?)", (name,))
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return int(cid)



def create_student(
    class_id: int,
    full_name: str,
    phone: str = "",
    payment_frequency: str = "monthly",
    *,
    address: Optional[str] = None,
    birth_date: Optional[str] = None,
    parent_name: Optional[str] = None,
    parent_phone: Optional[str] = None,
    notes: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> int:
    conn = connect()
    cur = conn.cursor()
    normalized_frequency = normalize_payment_frequency(payment_frequency)
    cur.execute(
        """
        INSERT INTO students(
            class_id,
            full_name,
            phone,
            payment_frequency,
            address,
            birth_date,
            parent_name,
            parent_phone,
            notes,
            payment_method
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            class_id,
            full_name,
            phone or None,
            normalized_frequency,
            address or None,
            birth_date or None,
            parent_name or None,
            parent_phone or None,
            notes or None,
            payment_method or None,
        ),
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return int(sid)


def update_student(
    student_id: int,
    full_name: str,
    phone: str,
    class_id: int,
    payment_frequency: str = "monthly",
    *,
    address: Optional[str] = None,
    birth_date: Optional[str] = None,
    parent_name: Optional[str] = None,
    parent_phone: Optional[str] = None,
    notes: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> None:
    conn = connect()
    normalized_frequency = normalize_payment_frequency(payment_frequency)
    conn.execute(
        """
        UPDATE students
        SET full_name = ?,
            phone = ?,
            class_id = ?,
            payment_frequency = ?,
            address = ?,
            birth_date = ?,
            parent_name = ?,
            parent_phone = ?,
            notes = ?,
            payment_method = ?
        WHERE id = ?
        """,
        (
            full_name,
            phone or None,
            class_id,
            normalized_frequency,
            address or None,
            birth_date or None,
            parent_name or None,
            parent_phone or None,
            notes or None,
            payment_method or None,
            student_id,
        ),
    )
    conn.commit()
    conn.close()


def get_payment_history_entry(history_id: int) -> Optional[dict]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            h.id,
            h.payment_id,
            h.student_id,
            COALESCE(s.full_name, h.student_name_snapshot, '[deleted student]') AS student_name,
            h.class_name_snapshot,
            COALESCE(c.name, h.class_name_snapshot, '[deleted class]') AS class_name,
            h.action,
            h.old_status,
            h.new_status,
            h.old_amount,
            h.new_amount,
            h.old_paid_date,
            h.new_paid_date,
            h.changed_by,
            u.username AS changed_by_username,
            h.changed_at,
            h.note
        FROM payment_history h
        LEFT JOIN students s ON s.id = h.student_id
        LEFT JOIN classes c ON c.id = s.class_id
        LEFT JOIN users u ON u.id = h.changed_by
        WHERE h.id = ?
        """,
        (history_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_payment_history_entry(
    *,
    payment_id: Optional[int],
    student_id: int,
    action: str,
    old_status: Optional[str],
    new_status: Optional[str],
    old_amount: Optional[float],
    new_amount: Optional[float],
    old_paid_date: Optional[str],
    new_paid_date: Optional[str],
    changed_by: int,
    note: str = "",
) -> int:
    """Admin helper to manually insert payment_history rows.

    This does not touch the `payments` table.
    """
    if new_status is not None and new_status not in ("paid", "unpaid"):
        raise ValueError("new_status must be paid or unpaid")
    if old_status is not None and old_status not in ("paid", "unpaid"):
        raise ValueError("old_status must be paid or unpaid")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT s.full_name AS student_name, c.name AS class_name
        FROM students s
        LEFT JOIN classes c ON c.id = s.class_id
        WHERE s.id = ?
        """,
        (student_id,),
    )
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        raise ValueError("Student not found")

    cur.execute(
        """
        INSERT INTO payment_history(
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
            note
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            payment_id,
            student_id,
            student_row["student_name"],
            student_row["class_name"],
            action,
            old_status,
            new_status,
            old_amount,
            new_amount,
            old_paid_date,
            new_paid_date,
            changed_by,
            note,
        ),
    )
    hid = cur.lastrowid
    conn.commit()
    conn.close()
    return int(hid)


def update_payment_history_entry(
    history_id: int,
    *,
    payment_id: Optional[int],
    student_id: int,
    action: str,
    old_status: Optional[str],
    new_status: Optional[str],
    old_amount: Optional[float],
    new_amount: Optional[float],
    old_paid_date: Optional[str],
    new_paid_date: Optional[str],
    changed_by: int,
    note: str = "",
) -> None:
    if new_status is not None and new_status not in ("paid", "unpaid"):
        raise ValueError("new_status must be paid or unpaid")
    if old_status is not None and old_status not in ("paid", "unpaid"):
        raise ValueError("old_status must be paid or unpaid")

    conn = connect()
    cur = conn.cursor()

    # Refresh snapshots based on current student/class
    cur.execute(
        """
        SELECT s.full_name AS student_name, c.name AS class_name
        FROM students s
        LEFT JOIN classes c ON c.id = s.class_id
        WHERE s.id = ?
        """,
        (student_id,),
    )
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        raise ValueError("Student not found")

    cur.execute(
        """
        UPDATE payment_history
        SET
            payment_id = ?,
            student_id = ?,
            student_name_snapshot = ?,
            class_name_snapshot = ?,
            action = ?,
            old_status = ?,
            new_status = ?,
            old_amount = ?,
            new_amount = ?,
            old_paid_date = ?,
            new_paid_date = ?,
            changed_by = ?,
            changed_at = datetime('now'),
            note = ?
        WHERE id = ?
        """,
        (
            payment_id,
            student_id,
            student_row["student_name"],
            student_row["class_name"],
            action,
            old_status,
            new_status,
            old_amount,
            new_amount,
            old_paid_date,
            new_paid_date,
            changed_by,
            note,
            history_id,
        ),
    )

    if cur.rowcount == 0:
        conn.close()
        raise ValueError("History entry not found")

    conn.commit()
    conn.close()


def delete_payment_history_entry(history_id: int) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM payment_history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()


def list_payment_history(student_id: Optional[int] = None):
    conn = connect()
    cur = conn.cursor()
    if student_id is None:
        cur.execute(
            """
         SELECT h.id,
             COALESCE(s.full_name, h.student_name_snapshot, '[deleted student]') AS student_name,
             COALESCE(c.name, h.class_name_snapshot, '[deleted class]') AS class_name,
                   h.action, h.old_status, h.new_status, h.old_amount, h.new_amount,
                   h.old_paid_date, h.new_paid_date, u.username AS changed_by,
                   h.changed_at, h.note
            FROM payment_history h
         LEFT JOIN students s ON s.id = h.student_id
         LEFT JOIN classes c ON c.id = s.class_id
            JOIN users u ON u.id = h.changed_by
            ORDER BY datetime(h.changed_at) DESC, h.id DESC
            """
        )
    else:
        cur.execute(
            """
         SELECT h.id,
             COALESCE(s.full_name, h.student_name_snapshot, '[deleted student]') AS student_name,
             COALESCE(c.name, h.class_name_snapshot, '[deleted class]') AS class_name,
                   h.action, h.old_status, h.new_status, h.old_amount, h.new_amount,
                   h.old_paid_date, h.new_paid_date, u.username AS changed_by,
                   h.changed_at, h.note
            FROM payment_history h
         LEFT JOIN students s ON s.id = h.student_id
         LEFT JOIN classes c ON c.id = s.class_id
            JOIN users u ON u.id = h.changed_by
            WHERE h.student_id = ?
            ORDER BY datetime(h.changed_at) DESC, h.id DESC
            """,
            (student_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            **row,
            "due_amount": compute_due_amount(row.get("payment_frequency")),
        }
        for row in [dict(r) for r in rows]
    ]


def compute_admin_graphs():
    conn = connect()
    cur = conn.cursor()

    # Money over time: sum new_amount for paid changes
    cur.execute(
        """
        SELECT substr(h.changed_at,1,10) AS day, SUM(h.new_amount) AS total
        FROM payment_history h
        WHERE h.new_status = 'paid'
        GROUP BY substr(h.changed_at,1,10)
        ORDER BY day
        """
    )
    money = [(r["day"], r["total"] or 0.0) for r in cur.fetchall()]

    # Status per class: count latest payment per student
    cur.execute(
        """
        WITH latest AS (
                    SELECT p.*, ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY p.id DESC) AS rn
          FROM payments p
        )
        SELECT c.name AS class_name,
               SUM(CASE WHEN l.status='paid' THEN 1 ELSE 0 END) AS paid_students,
               SUM(CASE WHEN l.status='unpaid' THEN 1 ELSE 0 END) AS unpaid_students
        FROM classes c
        JOIN students s ON s.class_id=c.id
        LEFT JOIN latest l ON l.student_id=s.id AND l.rn=1
        GROUP BY c.id
        ORDER BY c.name
        """
    )
    status_class = [dict(r) for r in cur.fetchall()]

    # Status per student: latest
    cur.execute(
        """
        WITH latest AS (
                    SELECT p.*, ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY p.id DESC) AS rn
          FROM payments p
        )
        SELECT s.id AS student_id, s.full_name AS student_name, c.name AS class_name,
               l.status AS latest_status, l.amount AS latest_amount, l.paid_date AS latest_paid_date
        FROM students s
        JOIN classes c ON c.id=s.class_id
        LEFT JOIN latest l ON l.student_id=s.id AND l.rn=1
        ORDER BY c.name, s.full_name
        """
    )
    status_student = [dict(r) for r in cur.fetchall()]

    conn.close()
    return money, status_class, status_student


def list_students_with_latest_status(class_id: Optional[int] = None):
    conn = connect()
    cur = conn.cursor()

    where_clause = ""
    params: tuple[Any, ...] = ()
    if class_id is not None:
        where_clause = "WHERE s.class_id = ?"
        params = (class_id,)

    cur.execute(
        f"""
        WITH latest AS (
            SELECT p.*, ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY p.id DESC) AS rn
            FROM payments p
        )
        SELECT
            s.id,
            c.name AS class_name,
            s.full_name,
            s.phone,
            s.payment_frequency,
            l.status AS latest_status,
            l.amount AS latest_amount,
            l.paid_date AS latest_paid_date
        FROM students s
        JOIN classes c ON c.id = s.class_id
        LEFT JOIN latest l ON l.student_id = s.id AND l.rn = 1
        {where_clause}
        ORDER BY c.name, s.full_name
        """,
        params,
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            **dict(r),
            "due_amount": compute_due_amount(r["payment_frequency"]),
        }
        for r in rows
    ]

