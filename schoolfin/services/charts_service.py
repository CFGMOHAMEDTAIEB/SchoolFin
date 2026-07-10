"""Chart generation for dashboard visualization."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from PIL import Image

from schoolfin.db.db import connect

# Use non-interactive backend for PyQt6
matplotlib.use("Agg")


def _fig_to_image_data(fig) -> BytesIO:
    """Convert matplotlib figure to image data.

    Saved as JPEG to match the dashboard rendering pipeline (QPixmap loaded from JPEG bytes).
    """
    buf = BytesIO()
    fig.savefig(buf, format="jpeg", bbox_inches="tight", dpi=80)
    buf.seek(0)
    plt.close(fig)
    return buf


def get_revenue_trend_chart() -> Optional[Image.Image]:
    """Generate revenue trend line chart (last 30 days)."""
    conn = connect()
    cur = conn.cursor()

    # Get daily revenue for last 30 days
    today = datetime.now()
    thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT
            COALESCE(paid_date, DATE('now')) as date,
            SUM(amount) as daily_revenue
        FROM payments
        WHERE status = 'paid' AND (paid_date IS NULL OR paid_date >= ?)
        GROUP BY COALESCE(paid_date, DATE('now'))
        ORDER BY COALESCE(paid_date, DATE('now'))
        """,
        (thirty_days_ago,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    dates = [r[0] for r in rows]
    revenues = [float(r[1]) for r in rows]

    fig, ax = plt.subplots(figsize=(10.4, 4.3), dpi=140)
    fig.patch.set_facecolor("#f7f9ff")
    ax.set_facecolor("#fcfdff")

    ax.plot(
        dates,
        revenues,
        color="#1d4ed8",
        linewidth=2.8,
        marker="o",
        markersize=6.5,
        markerfacecolor="#ffffff",
        markeredgewidth=1.8,
        markeredgecolor="#1d4ed8",
    )
    ax.fill_between(range(len(dates)), revenues, color="#1d4ed8", alpha=0.18)

    ax.set_title(
        "Tendance des revenus (30 derniers jours)",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    ax.set_xlabel("Date", fontsize=11, color="#475569")
    ax.set_ylabel("Montant (€)", fontsize=11, color="#475569")
    ax.set_axisbelow(True)
    ax.grid(True, which="major", axis="both", color="#dbeafe", linewidth=0.8, alpha=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#dbeafe")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=35, ha="right")
    ax.tick_params(axis="both", colors="#475569", labelsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", " ")))
    plt.tight_layout()

    return Image.open(_fig_to_image_data(fig))


def get_payment_status_by_class_chart() -> Optional[Image.Image]:
    """Generate bar chart of payment status by class."""
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.name,
            SUM(CASE WHEN p.status = 'paid' THEN 1 ELSE 0 END) as paid,
            SUM(CASE WHEN p.status = 'unpaid' THEN 1 ELSE 0 END) as unpaid
        FROM classes c
        LEFT JOIN students s ON s.class_id = c.id
        LEFT JOIN payments p ON p.student_id = s.id
        GROUP BY c.id, c.name
        ORDER BY c.name
        """
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    classes = [r[0] for r in rows]
    paid = [int(r[1]) for r in rows]
    unpaid = [int(r[2]) for r in rows]

    fig, ax = plt.subplots(figsize=(10.4, 4.3), dpi=140)
    fig.patch.set_facecolor("#f7f9ff")
    ax.set_facecolor("#fcfdff")
    x = np.arange(len(classes))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2,
        paid,
        width,
        label="Payés",
        color="#16a34a",
        edgecolor="#166534",
        linewidth=1.2,
    )
    bars2 = ax.bar(
        x + width / 2,
        unpaid,
        width,
        label="Non payés",
        color="#ef4444",
        edgecolor="#b91c1c",
        linewidth=1.2,
    )

    ax.set_title("Statut des paiements par classe", fontsize=14, fontweight="bold", color="#0f172a", pad=10)
    ax.set_xlabel("Classe", fontsize=11, color="#475569")
    ax.set_ylabel("Nombre d'élèves", fontsize=11, color="#475569")
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=35, ha="right")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.55, axis="y", color="#dbeafe")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#dbeafe")
    ax.tick_params(axis="both", colors="#475569", labelsize=10)
    ax.legend(frameon=False, fontsize=10)
    for bars in (bars1, bars2):
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(paid + unpaid) * 0.01,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#334155",
            )

    plt.tight_layout()
    return Image.open(_fig_to_image_data(fig))


def get_revenue_vs_expenses_chart() -> Optional[Image.Image]:
    """Generate bar chart of revenue vs expenses by class."""
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.name,
            COALESCE(SUM(CASE WHEN p.status = 'paid' THEN p.amount ELSE 0 END), 0) as revenue,
            COALESCE(SUM(p.amount), 0) as total_amount
        FROM classes c
        LEFT JOIN students s ON s.class_id = c.id
        LEFT JOIN payments p ON p.student_id = s.id
        GROUP BY c.id, c.name
        ORDER BY c.name
        """
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    classes = [r[0] for r in rows]

    revenues: list[float] = []
    totals: list[float] = []
    for r in rows:
        # Be defensive: even if SQL should COALESCE, tolerate unexpected None.
        rev = r[1]
        tot = r[2]
        revenues.append(float(rev) if rev is not None else 0.0)
        totals.append(float(tot) if tot is not None else 0.0)

    expenses = [t - rev for t, rev in zip(totals, revenues)]

    fig, ax = plt.subplots(figsize=(10.4, 4.3), dpi=140)
    fig.patch.set_facecolor("#f7f9ff")
    ax.set_facecolor("#fcfdff")
    x = np.arange(len(classes))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2,
        revenues,
        width,
        label="Encaissements",
        color="#2563eb",
        edgecolor="#1d4ed8",
        linewidth=1.2,
    )
    bars2 = ax.bar(
        x + width / 2,
        expenses,
        width,
        label="Non encaissés",
        color="#f59e0b",
        edgecolor="#b45309",
        linewidth=1.2,
    )

    ax.set_title("Encaissements vs Non encaissés par classe", fontsize=14, fontweight="bold", color="#0f172a", pad=10)
    ax.set_xlabel("Classe", fontsize=11, color="#475569")
    ax.set_ylabel("Montant (€)", fontsize=11, color="#475569")
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=35, ha="right")
    ax.set_axisbelow(True)
    ax.grid(True, alpha=0.55, axis="y", color="#dbeafe")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#dbeafe")
    ax.tick_params(axis="both", colors="#475569", labelsize=10)
    ax.legend(frameon=False, fontsize=10)

    plt.tight_layout()
    return Image.open(_fig_to_image_data(fig))


def get_payment_distribution_chart() -> Optional[Image.Image]:
    """Generate pie chart of payment distribution."""
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            status,
            COUNT(*) as count
        FROM payments
        GROUP BY status
        """
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    # Build slices and labels from the exact same ordered dataset
    pairs = [(r[0], r[1]) for r in rows]
    raw_statuses = [s for s, _ in pairs]
    sizes = [int(c) if c is not None else 0 for _, c in pairs]

    status_label_map = {
        "paid": "Payés",
        "unpaid": "Non payés",
    }
    labels = [status_label_map.get(s, str(s)) for s in raw_statuses]

    # matplotlib requires labels length == sizes length
    if len(labels) != len(sizes):
        # Fallback: if something weird happens, regenerate labels by index.
        labels = [str(raw_statuses[i]) if i < len(raw_statuses) else "" for i in range(len(sizes))]

    # Ensure colors length matches number of slices
    base_colors = ["#4CAF50", "#F44336", "#2196F3", "#FF9800", "#9C27B0", "#00BCD4"]
    colors = [base_colors[i % len(base_colors)] for i in range(len(sizes))]

    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=140)
    fig.patch.set_facecolor("#f7f9ff")
    ax.set_facecolor("#fcfdff")
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.68,
        labeldistance=1.1,
        wedgeprops={"width": 0.62, "edgecolor": "white", "linewidth": 1.2},
        textprops={"fontsize": 10, "color": "#334155"},
    )
    ax.set_title("Distribution du statut des paiements", fontsize=14, fontweight="bold", color="#0f172a", pad=12)

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")
        autotext.set_fontsize(9)

    plt.tight_layout()
    return Image.open(_fig_to_image_data(fig))


def get_enrollment_trend_chart() -> Optional[Image.Image]:
    """Generate enrollment trend chart (cumulative)."""
    conn = connect()
    cur = conn.cursor()

    # Get cumulative student count by creation date
    cur.execute(
        """
        SELECT
            DATE(created_at) as date,
            COUNT(*) as daily_count
        FROM students
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
        """
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    dates = [r[0] for r in rows]
    daily_counts = [int(r[1]) for r in rows]
    cumulative = []
    total = 0
    for count in daily_counts:
        total += count
        cumulative.append(total)

    fig, ax = plt.subplots(figsize=(10.4, 4.3), dpi=140)
    fig.patch.set_facecolor("#f7f9ff")
    ax.set_facecolor("#fcfdff")
    ax.plot(
        dates,
        cumulative,
        color="#7c3aed",
        linewidth=2.8,
        marker="s",
        markersize=6.5,
        markerfacecolor="#ffffff",
        markeredgewidth=1.8,
        markeredgecolor="#7c3aed",
    )
    ax.fill_between(range(len(dates)), cumulative, color="#7c3aed", alpha=0.16)

    ax.set_title("Tendance des inscriptions", fontsize=14, fontweight="bold", color="#0f172a", pad=10)
    ax.set_xlabel("Date", fontsize=11, color="#475569")
    ax.set_ylabel("Nombre d'élèves", fontsize=11, color="#475569")
    ax.set_axisbelow(True)
    ax.grid(True, which="major", axis="both", color="#e9d5ff", linewidth=0.8, alpha=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#e9d5ff")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=35, ha="right")
    ax.tick_params(axis="both", colors="#475569", labelsize=10)
    plt.tight_layout()

    return Image.open(_fig_to_image_data(fig))
