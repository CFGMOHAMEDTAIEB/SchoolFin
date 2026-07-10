from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from schoolfin.services.payment_service import (
    get_student_latest_payment,
    list_classes,
    list_students_by_class,
)
from schoolfin.services.invoice_service import generate_invoice_pdf


class PrintExtractPage(QWidget):
    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self._search_text = ""
        self._students_data = []

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Imprimer l'extrait (Facture de paiement)"))

        # Filters
        filter_row = QHBoxLayout()
        layout.addLayout(filter_row)

        filter_row.addWidget(QLabel("Classe:"))

        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.class_filter)

        filter_row.addWidget(QLabel("Étudiant:"))

        self.students_combo = QComboBox()
        self.students_combo.currentIndexChanged.connect(self._on_student_changed)
        filter_row.addWidget(self.students_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un étudiant")
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_row.addWidget(self.search_input)

        # Facture display
        form = QFormLayout()
        layout.addLayout(form)

        self.lbl_student = QLabel("-")
        self.lbl_class = QLabel("-")
        self.lbl_status = QLabel("-")
        self.lbl_amount = QLabel("-")
        self.lbl_paid_date = QLabel("-")
        self.lbl_payment_id = QLabel("-")

        form.addRow(QLabel("Étudiant"), self.lbl_student)
        form.addRow(QLabel("Classe"), self.lbl_class)
        form.addRow(QLabel("Statut"), self.lbl_status)
        form.addRow(QLabel("Montant"), self.lbl_amount)
        form.addRow(QLabel("Date de paiement"), self.lbl_paid_date)
        form.addRow(QLabel("ID de paiement (dernier)"), self.lbl_payment_id)

        layout.addSpacing(10)

        # Controls
        self.btn_print = QPushButton("Générer la facture PDF")
        self.btn_print.setEnabled(True)
        self.btn_print.clicked.connect(self._on_print_clicked)
        layout.addWidget(self.btn_print)

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

    def _on_search_changed(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_search_filter()

    def refresh(self):
        class_id = self.class_filter.currentData()
        self._students_data = list_students_by_class(class_id)
        self._apply_search_filter()

    def _apply_search_filter(self):
        self.students_combo.blockSignals(True)
        self.students_combo.clear()

        if not self._students_data:
            self._render_empty_facture()
            self.students_combo.blockSignals(False)
            return

        for s in self._students_data:
            haystack = " ".join(
                [str(s.get("full_name", "")), str(s.get("class_name", "")), str(s.get("id", ""))]
            ).lower()
            if self._search_text and self._search_text not in haystack:
                continue
            self.students_combo.addItem(f"{s['full_name']} ({s['class_name']})", s["id"])

        if self.students_combo.count() > 0:
            self.students_combo.setCurrentIndex(0)
        self.students_combo.blockSignals(False)
        self._on_student_changed()

    def _render_empty_facture(self):
        self.lbl_student.setText("-")
        self.lbl_class.setText("-")
        self.lbl_status.setText("Non Payée")
        self.lbl_amount.setText("0.0")
        self.lbl_paid_date.setText("-")
        self.lbl_payment_id.setText("-")

    def _on_student_changed(self):
        student_id = self.students_combo.currentData()
        if student_id is None:
            self._render_empty_facture()
            return

        try:
            latest = get_student_latest_payment(int(student_id))
        except Exception as e:
            QMessageBox.critical(self, "Print Extract", str(e))
            self._render_empty_facture()
            return

        # Extract "(Student Name) (Class Name)" from combo text
        combo_text = self.students_combo.currentText()
        student_name = combo_text.split(" (", 1)[0] if " (" in combo_text else combo_text
        class_name = ""
        if " (" in combo_text and combo_text.endswith(")"):
            class_name = combo_text.split(" (", 1)[1][:-1]

        if not latest:
            # No payment rows for this student yet => treat as unpaid
            self.lbl_student.setText(student_name or "-")
            self.lbl_class.setText(class_name or "-")
            self.lbl_status.setText("Impayée")
            self.lbl_amount.setText("0.0")
            self.lbl_paid_date.setText("-")
            self.lbl_payment_id.setText("-")
            return

        # `latest` is a dict from payments table (SELECT * from payments), so it usually won't contain
        # student/class snapshots. We rely on the selected combo text for those.
        self.lbl_student.setText(student_name or "-")
        self.lbl_class.setText(class_name or "-")
        status = latest.get("status") or "unpaid"
        self.lbl_status.setText("Payée" if status == "paid" else "Non Payée")

        amount = latest.get("amount")
        self.lbl_amount.setText("-" if amount is None else str(float(amount)))

        paid_date = latest.get("paid_date")
        self.lbl_paid_date.setText("-" if not paid_date else str(paid_date))

        payment_id = latest.get("id")
        self.lbl_payment_id.setText("-" if payment_id is None else str(payment_id))

    def _on_print_clicked(self):
        student_id = self.students_combo.currentData()
        if student_id is None:
            QMessageBox.warning(self, "Imprimer l'extrait", "Veuillez d'abord sélectionner un étudiant")
            return

        try:
            latest = get_student_latest_payment(int(student_id))
        except Exception as e:
            QMessageBox.critical(self, "Imprimer l'extrait", str(e))
            return

        combo_text = self.students_combo.currentText()
        student_name = combo_text.split(" (", 1)[0] if " (" in combo_text else combo_text
        class_name = ""
        if " (" in combo_text and combo_text.endswith(")"):
            class_name = combo_text.split(" (", 1)[1][:-1]

        status = "unpaid"
        amount = 0.0
        paid_date = "-"
        payment_id = "-"

        if latest:
            status = latest.get("status") or "unpaid"
            amt = latest.get("amount")
            amount = 0.0 if amt is None else float(amt)
            paid_date = latest.get("paid_date") or "-"
            payment_id = latest.get("id") or "-"

        default_name = f"facture_{student_name or 'etudiant'}_{class_name or 'classe'}.pdf".replace(
            "/", "-"
        ).replace("\\", "-").replace(":", "-")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer la facture en PDF",
            default_name,
            "Fichiers PDF (*.pdf)",
        )
        if not file_path:
            return

        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            generate_invoice_pdf(
                file_path=file_path,
                student_name=student_name or "-",
                class_name=class_name or "-",
                amount=amount,
                paid_date=paid_date if paid_date != "-" else None,
                payment_id=payment_id,
                status=status,
                student_id=int(student_id),
            )
            QMessageBox.information(self, "Succès", f"Facture enregistrée avec succès à:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer la facture:\n{str(e)}")

