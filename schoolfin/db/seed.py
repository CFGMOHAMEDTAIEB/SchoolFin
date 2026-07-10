"""Seed database with sample data for development and testing."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from random import choice, randint, uniform

from schoolfin.db.db import connect, sha256


def reset_database() -> None:
    """Reset and seed the database with sample data."""
    conn = connect()
    cur = conn.cursor()

    # Clear existing data (keep schema)
    cur.execute("DELETE FROM payment_history")
    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM students")
    cur.execute("DELETE FROM classes")
    cur.execute("DELETE FROM users")

    # Reset sequences
    cur.execute("DELETE FROM sqlite_sequence")

    # Seed users
    users = [
        ("admin", "admin123", "admin"),
        ("financial", "financial123", "financial"),
    ]
    cur.executemany(
        "INSERT INTO users(username, password_hash, role) VALUES (?,?,?)",
        [(u, sha256(pw), role) for (u, pw, role) in users],
    )

    # Seed classes
    classes = [
        "CM2 - Alpha",
        "CM2 - Beta",
        "6ème - Gamma",
        "6ème - Delta",
        "5ème - Epsilon",
        "5ème - Zeta",
    ]
    cur.executemany("INSERT INTO classes(name) VALUES (?)", [(c,) for c in classes])
    conn.commit()

    # Get class IDs
    cur.execute("SELECT id FROM classes ORDER BY id")
    class_ids = [r[0] for r in cur.fetchall()]

    # Seed students
    first_names = [
        "Jean", "Marie", "Lucas", "Sophie", "Marc", "Anne",
        "Pierre", "Claire", "Thomas", "Julie", "David", "Emma",
        "Paul", "Lucie", "Michel", "Zoe", "Andre", "Nina",
        "Claude", "Lea",
    ]
    last_names = [
        "Dupont", "Martin", "Bernard", "Thomas", "Robert", "Richard",
        "Petit", "Durand", "Lefevre", "Moreau", "Simon", "Laurent",
        "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux",
    ]

    students = []
    for class_id in class_ids:
        for _ in range(randint(8, 12)):
            fname = choice(first_names)
            lname = choice(last_names)
            phone = f"+33 {randint(6,9)} {randint(10000000, 99999999)}"
            students.append((class_id, f"{fname} {lname}", phone))

    cur.executemany(
        "INSERT INTO students(class_id, full_name, phone) VALUES (?,?,?)",
        students,
    )
    conn.commit()

    # Get student and user IDs
    cur.execute("SELECT id FROM students ORDER BY id")
    student_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM users WHERE role='admin'")
    admin_id = cur.fetchone()[0]

    # Seed payments with varied dates for charting
    payments = []
    today = datetime.now()
    
    for student_id in student_ids:
        # Each student has one payment record (most recent)
        status = choice(["paid", "unpaid"])
        amount = uniform(100, 500)
        
        # Create some historic dates (last 30 days)
        days_ago = randint(0, 30)
        payment_date = None
        if status == "paid":
            payment_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        payments.append((student_id, amount, payment_date, status, admin_id))

    cur.executemany(
        "INSERT INTO payments(student_id, amount, paid_date, status, created_by) VALUES (?,?,?,?,?)",
        payments,
    )
    conn.commit()

    # Create some payment history for audit trail
    cur.execute("SELECT id FROM payments LIMIT 5")
    sample_payments = [r[0] for r in cur.fetchall()]
    
    for payment_id in sample_payments:
        if randint(0, 1) == 0:
            # Add a status change history
            cur.execute(
                """
                INSERT INTO payment_history
                (payment_id, student_id, action, old_status, new_status, changed_by, note)
                SELECT ?, student_id, 'status_change', 'unpaid', 'paid', ?, 'Manual update'
                FROM payments WHERE id = ?
                """,
                (payment_id, admin_id, payment_id),
            )

    conn.commit()
    conn.close()


def get_sample_data_summary() -> dict:
    """Get a summary of the seeded data."""
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as count FROM students")
    total_students = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM classes")
    total_classes = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'paid'")
    paid_count = cur.fetchone()["count"]

    cur.execute("SELECT SUM(amount) as total FROM payments WHERE status = 'paid'")
    total_revenue = cur.fetchone()["total"] or 0

    conn.close()

    return {
        "total_students": total_students,
        "total_classes": total_classes,
        "paid_students": paid_count,
        "unpaid_students": total_students - paid_count,
        "total_revenue": total_revenue,
    }
