from __future__ import annotations

from typing import Optional
from io import BytesIO

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QFrame,
    QScrollArea,
)

from schoolfin.services.payment_service import compute_admin_graphs
from schoolfin.services.charts_service import (
    get_revenue_trend_chart,
    get_payment_status_by_class_chart,
    get_revenue_vs_expenses_chart,
    get_payment_distribution_chart,
    get_enrollment_trend_chart,
)


class DashboardPage(QWidget):
    """Admin/financial dashboard with styled KPIs and chart images."""

    def __init__(self, role: str = "admin"):
        super().__init__()
        self.role = role

        self._money_total_label: Optional[QLabel] = None
        self._paid_count_label: Optional[QLabel] = None
        self._unpaid_count_label: Optional[QLabel] = None
        self._total_students_label: Optional[QLabel] = None
        self._total_classes_label: Optional[QLabel] = None
        self._collection_rate_label: Optional[QLabel] = None

        # Map chart id -> QLabel where we render the image
        self._chart_labels: dict[str, QLabel] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(outer_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(16)

        outer_layout.addWidget(scroll)
        scroll.setWidget(content)

        # --- Header ---
        title = QLabel("Tableau de bord Administrateur" if self.role == "admin" else "Tableau de bord Financier")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #10213a;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Bienvenue, voici un aperçu de l'activité de l'établissement aujourd'hui."
            if self.role == "admin"
            else "Aperçu des encaissements et du suivi des paiements."
        )
        subtitle.setStyleSheet("color: #6b778e; font-size: 13px;")
        layout.addWidget(subtitle)

        # --- KPI Cards Row 1 ---
        kpi_row1 = QHBoxLayout()
        layout.addLayout(kpi_row1)

        def card(title: str, label_name: str, bg_color: str = "#f5f7ff") -> tuple[QFrame, QLabel]:
            c = QFrame()
            c.setFrameShape(QFrame.Shape.StyledPanel)
            c.setMinimumHeight(100)
            c.setStyleSheet(
                f"background: {bg_color}; border-radius: 12px; border: 1px solid #e0e5f0;"
            )

            v = QVBoxLayout(c)
            v.setContentsMargins(16, 14, 16, 14)
            v.setSpacing(8)

            head = QLabel(title)
            head.setStyleSheet("font-weight: 700; color: #16326f; font-size: 12px;")

            value = QLabel("—")
            value.setObjectName(label_name)
            value.setAlignment(Qt.AlignmentFlag.AlignLeft)
            value.setStyleSheet("font-weight: 900; font-size: 28px; color: #0d2470;")

            v.addWidget(head)
            v.addWidget(value)
            return c, value

        money_card, self._money_total_label = card("Montant total encaissé", "kpi_money", "#e8f5e9")
        paid_card, self._paid_count_label = card("Élèves payés", "kpi_paid", "#e3f2fd")
        unpaid_card, self._unpaid_count_label = card("Élèves non payés", "kpi_unpaid", "#fff3e0")
        total_card, self._total_students_label = card("Total élèves", "kpi_total", "#f3e5f5")

        kpi_row1.addWidget(money_card)
        kpi_row1.addWidget(paid_card)
        kpi_row1.addWidget(unpaid_card)
        kpi_row1.addWidget(total_card)

        # --- KPI Cards Row 2 ---
        kpi_row2 = QHBoxLayout()
        layout.addLayout(kpi_row2)

        classes_card, self._total_classes_label = card("Nombre de classes", "kpi_classes", "#fce4ec")
        collection_card, self._collection_rate_label = card(
            "Taux de collecte", "kpi_collection", "#e0f2f1"
        )
        alert_card, _ = card("Alertes urgentes", "kpi_alerts", "#ffebee")
        trend_card, _ = card("Tendance (7j)", "kpi_trend", "#f1f8e9")

        kpi_row2.addWidget(classes_card)
        kpi_row2.addWidget(collection_card)
        kpi_row2.addWidget(alert_card)
        kpi_row2.addWidget(trend_card)

        # --- Charts Section ---
        charts_title = QLabel("Graphiques & Visualisations")
        charts_title.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #10213a; margin-top: 20px;"
        )
        layout.addWidget(charts_title)

        # Revenue Trend
        revenue_frame = self._make_chart_container("Tendance des revenus (30 jours)")
        layout.addWidget(revenue_frame)
        self._chart_labels["revenue_trend"] = revenue_frame.findChild(QLabel, "chart_image")

        # Payment Status by Class
        status_frame = self._make_chart_container("Statut des paiements par classe")
        layout.addWidget(status_frame)
        self._chart_labels["payment_status"] = status_frame.findChild(QLabel, "chart_image")

        # Revenue vs Expenses
        rev_exp_frame = self._make_chart_container("Revenus vs Non encaissés par classe")
        layout.addWidget(rev_exp_frame)
        self._chart_labels["revenue_vs_expenses"] = rev_exp_frame.findChild(QLabel, "chart_image")

        # Distribution & Enrollment (side by side)
        charts_row = QHBoxLayout()
        layout.addLayout(charts_row)

        dist_frame = self._make_chart_container("Distribution du statut", height=280)
        enroll_frame = self._make_chart_container("Tendance des inscriptions", height=280)

        charts_row.addWidget(dist_frame)
        charts_row.addWidget(enroll_frame)

        self._chart_labels["distribution"] = dist_frame.findChild(QLabel, "chart_image")
        self._chart_labels["enrollment"] = enroll_frame.findChild(QLabel, "chart_image")

        layout.addStretch()

    def _make_chart_container(self, title: str, height: int = 320) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setMinimumHeight(height)
        frame.setStyleSheet(
            "background: white; border-radius: 14px; border: 1px solid #e0e5f0;"
        )
        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(15, 23, 42, 40))
        frame.setGraphicsEffect(shadow)

        v = QVBoxLayout(frame)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        t = QLabel(title)
        t.setStyleSheet("font-weight: 800; color: #10213a; font-size: 14px;")

        chart_label = QLabel()
        chart_label.setObjectName("chart_image")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_label.setStyleSheet("color: #6b778e; background: rgba(13, 36, 112, 0.03);")
        chart_label.setText("Chargement du graphique...")

        # Keep some minimum height so scaling behaves nicely
        chart_label.setMinimumHeight(int(height * 0.72))
        v.addWidget(t)
        v.addWidget(chart_label, 1)
        return frame

    def set_search_text(self, text: str) -> None:
        return None

    def refresh(self):
        """Update KPIs and charts."""
        if self.role != "admin":
            return

        money, status_class, status_student = compute_admin_graphs()

        money_total = sum(float(v) or 0.0 for _, v in money)
        paid_count = sum(1 for r in status_student if (r.get("latest_status") or "") == "paid")
        unpaid_count = sum(1 for r in status_student if (r.get("latest_status") or "") == "unpaid")
        total_students = paid_count + unpaid_count
        total_classes = len(status_class) if status_class else 0
        collection_rate = (paid_count / total_students * 100) if total_students > 0 else 0

        if self._money_total_label:
            self._money_total_label.setText(f"{money_total:,.2f} €".replace(",", " "))
        if self._paid_count_label:
            self._paid_count_label.setText(str(paid_count))
        if self._unpaid_count_label:
            self._unpaid_count_label.setText(str(unpaid_count))
        if self._total_students_label:
            self._total_students_label.setText(str(total_students))
        if self._total_classes_label:
            self._total_classes_label.setText(str(total_classes))
        if self._collection_rate_label:
            self._collection_rate_label.setText(f"{collection_rate:.1f}%")

        # Update charts
        self._update_chart("revenue_trend", get_revenue_trend_chart())
        self._update_chart("payment_status", get_payment_status_by_class_chart())
        self._update_chart("revenue_vs_expenses", get_revenue_vs_expenses_chart())
        self._update_chart("distribution", get_payment_distribution_chart())
        self._update_chart("enrollment", get_enrollment_trend_chart())

    def _update_chart(self, chart_name: str, image) -> None:
        """Render a chart image into its QLabel."""
        if chart_name not in self._chart_labels or image is None:
            return

        label = self._chart_labels[chart_name]

        # QPixmap.loadFromData expects encoded bytes (PNG/JPEG/etc).
        # Some Pillow builds (especially in packaged apps) may not include PNG encoder.
        pixmap = QPixmap()

        # Always encode as JPEG to avoid environments where Pillow lacks PNG encoder support.
        # (This is the root cause of: OSError: encoder png not available / png_encoder missing.)
        if getattr(image, "mode", "") in ("RGBA", "LA", "P"):
            image_for_jpeg = image.convert("RGB")
        else:
            image_for_jpeg = image

        buf = BytesIO()
        image_for_jpeg.save(buf, format="JPEG")
        pixmap.loadFromData(buf.getvalue())

        if pixmap.isNull():
            label.setText("Erreur lors du chargement du graphique")
            return

        # Fit to label keeping aspect ratio.
        # Use current label size; fallback to width if size is not ready yet.
        target_w = max(320, label.width())
        target_h = max(220, label.height())
        scaled = pixmap.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(scaled)
        label.setText("")



