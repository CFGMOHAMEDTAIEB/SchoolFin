from __future__ import annotations

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QDateEdit,
)

from schoolfin.auth.session import get_session
from schoolfin.services.payment_service import (
    compute_due_amount,
    format_payment_frequency,
    list_classes,
    list_students_with_latest_status,
    set_payment_status,
)


class PaymentsPage(QWidget):
    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self.session = get_session()
        self._search_text = ""
        self._students_data = []

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Paiements / Statut"))

        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.class_filter)

        self.students_combo = QComboBox()
        self.students_combo.currentIndexChanged.connect(self._update_amount_for_selected_student)
        layout.addWidget(self.students_combo)

        self.status_paid = QRadioButton("Payé")
        self.status_unpaid = QRadioButton("Impayé")
        self.status_paid.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.status_paid)
        bg.addButton(self.status_unpaid)

        row = QVBoxLayout()
        row.addWidget(self.status_paid)
        row.addWidget(self.status_unpaid)
        layout.addLayout(row)

        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Montant")
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        layout.addWidget(QLabel("Montant (pour un paiement payé)"))
        layout.addWidget(self.amount)
        layout.addWidget(QLabel("Date de paiement (pour un paiement payé)"))
        layout.addWidget(self.date)

        self.btn_set = QPushButton("Enregistrer le statut")
        self.btn_set.clicked.connect(self.on_save)
        layout.addWidget(self.btn_set)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID étudiant", "Nom", "Classe", "Fréquence", "À payer", "Dernier statut", "Date de paiement"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        if self.role != "admin" and self.role != "financial":
            self.btn_set.setDisabled(True)

        if self.role == "financial" or self.role == "admin":
            pass

        self._reload_class_filter()
        self.refresh()

    def _reload_class_filter(self):
        selected = self.class_filter.currentData()
        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItem("Toutes les classes", None)
        for c in list_classes():
            self.class_filter.addItem(c["name"], c["id"])
        if selected is not None:
            idx = self.class_filter.findData(selected)
            if idx >= 0:
                self.class_filter.setCurrentIndex(idx)
        self.class_filter.blockSignals(False)

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_search_filter()

    def refresh(self):
        self._reload_class_filter()
        class_id = self.class_filter.currentData()
        self._students_data = list_students_with_latest_status(class_id)
        self._apply_search_filter()

    def _apply_search_filter(self):
        self.table.setRowCount(0)
        self.students_combo.clear()
        query = self._search_text
        for r in self._students_data:
            haystack = " ".join(
                [
                    str(r.get("full_name", "")),
                    str(r.get("class_name", "")),
                    str(r.get("latest_status", "")),
                    str(r.get("latest_amount", "")),
                    str(r.get("latest_paid_date", "")),
                    str(r.get("id", "")),
                ]
            ).lower()
            if query and query not in haystack:
                continue
            self.students_combo.addItem(f"{r['full_name']} ({r['class_name']})", r["id"])
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["full_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["class_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(format_payment_frequency(r.get("payment_frequency"))))
            due_amount = r.get("due_amount")
            self.table.setItem(row, 4, QTableWidgetItem(f"{due_amount:.2f}" if due_amount is not None else "0.00"))
            self.table.setItem(row, 5, QTableWidgetItem((r.get("latest_status") or "")))
            self.table.setItem(row, 6, QTableWidgetItem((r.get("latest_paid_date") or "")))

        self._update_amount_for_selected_student()

    def _update_amount_for_selected_student(self):
        student_id = self.students_combo.currentData()
        if student_id is None:
            return

        for row_data in self._students_data:
            if row_data.get("id") == student_id:
                due_amount = row_data.get("due_amount")
                if due_amount is None:
                    due_amount = compute_due_amount(row_data.get("payment_frequency"))
                self.amount.setText(f"{due_amount:.2f}")
                return

    def on_save(self):
        if not self.session:
            return
        student_id = self.students_combo.currentData()
        if student_id is None:
            QMessageBox.warning(self, "Paiements", "Sélectionnez un élève")
            return

        status = "paid" if self.status_paid.isChecked() else "unpaid"
        note = ""

        amount = 0.0
        paid_date = None
        if status == "paid":
            try:
                amount = float(self.amount.text().strip() or "0")
            except ValueError:
                QMessageBox.warning(self, "Paiements", "Montant invalide")
                return
            paid_date = self.date.date().toString("yyyy-MM-dd")

        try:
            set_payment_status(
                student_id=int(student_id),
                status=status,
                amount=amount,
                paid_date=paid_date,
                changed_by=self.session.user_id,
                note=note,
            )
        except Exception as e:
            QMessageBox.critical(self, "Payments", str(e))
            return

        QMessageBox.information(self, "Paiements", "Enregistré")
        main = self.window()
        if hasattr(main, "notify_data_changed"):
            main.notify_data_changed("payments")
        else:
            self.refresh()

