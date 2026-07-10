from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from schoolfin.services.payment_service import (
    create_payment_history_entry,
    delete_payment_history_entry,
    get_payment_history_entry,
    list_payment_history,
    update_payment_history_entry,
)


class HistoryPage(QWidget):
    def __init__(self, role: str):
        super().__init__()

        self._restricted = role != "admin"
        self._search_text = ""
        self._history_data = []
        self._history_id_input: Optional[QLineEdit] = None
        self._student_id_input: Optional[QLineEdit] = None
        self._action_input: Optional[QLineEdit] = None
        self._old_status_input: Optional[QComboBox] = None
        self._new_status_input: Optional[QComboBox] = None
        self._old_amount_input: Optional[QLineEdit] = None
        self._new_amount_input: Optional[QLineEdit] = None
        self._old_paid_date_input: Optional[QLineEdit] = None
        self._new_paid_date_input: Optional[QLineEdit] = None
        self._note_input: Optional[QLineEdit] = None

        if self._restricted:
            layout = QVBoxLayout()
            self.setLayout(layout)
            layout.addWidget(QLabel("Historique des paiements (réservé à l'administrateur)"))
            layout.addWidget(QLabel("L'historique est réservé aux administrateurs."))
            return

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Historique des paiements (administration)"))

        # --- CRUD controls ---
        form = QFormLayout()
        layout.addLayout(form)

        self._history_id_input = QLineEdit()
        self._history_id_input.setPlaceholderText("ID d'historique (pour charger, modifier ou supprimer)")
        form.addRow("ID d'historique", self._history_id_input)

        self._student_id_input = QLineEdit()
        self._student_id_input.setPlaceholderText("ID de l'élève (pour créer ou modifier)")
        form.addRow("ID de l'élève", self._student_id_input)

        self._action_input = QLineEdit()
        self._action_input.setPlaceholderText("action (ex. set_status)")
        form.addRow("Action", self._action_input)

        self._old_status_input = QComboBox()
        self._old_status_input.addItem("(null)", None)
        self._old_status_input.addItem("paid", "paid")
        self._old_status_input.addItem("unpaid", "unpaid")
        form.addRow("Ancien statut", self._old_status_input)

        self._new_status_input = QComboBox()
        self._new_status_input.addItem("(null)", None)
        self._new_status_input.addItem("paid", "paid")
        self._new_status_input.addItem("unpaid", "unpaid")
        form.addRow("Nouveau statut", self._new_status_input)

        self._old_amount_input = QLineEdit()
        self._old_amount_input.setPlaceholderText("Ancien montant")
        form.addRow("Ancien montant", self._old_amount_input)

        self._new_amount_input = QLineEdit()
        self._new_amount_input.setPlaceholderText("Nouveau montant")
        form.addRow("Nouveau montant", self._new_amount_input)

        self._old_paid_date_input = QLineEdit()
        self._old_paid_date_input.setPlaceholderText("Ancienne date de paiement (yyyy-MM-dd) ou vide")
        form.addRow("Ancienne date", self._old_paid_date_input)

        self._new_paid_date_input = QLineEdit()
        self._new_paid_date_input.setPlaceholderText("Nouvelle date de paiement (yyyy-MM-dd) ou vide")
        form.addRow("Nouvelle date", self._new_paid_date_input)

        self._note_input = QLineEdit()
        self._note_input.setPlaceholderText("Note")
        form.addRow("Note", self._note_input)

        btn_row = QHBoxLayout()
        layout.addLayout(btn_row)

        self._btn_load = QPushButton("Charger par ID")
        self._btn_load.clicked.connect(self.on_load)
        btn_row.addWidget(self._btn_load)

        self._btn_create = QPushButton("Créer")
        self._btn_create.clicked.connect(self.on_create)
        btn_row.addWidget(self._btn_create)

        self._btn_update = QPushButton("Modifier")
        self._btn_update.clicked.connect(self.on_update)
        btn_row.addWidget(self._btn_update)

        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.clicked.connect(self.on_delete)
        btn_row.addWidget(self._btn_delete)

        # --- History table ---
        self.table = QTableWidget(0, 14)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Élève",
                "Classe",
                "Action",
                "Ancien statut",
                "Nouveau statut",
                "Ancien montant",
                "Nouveau montant",
                "Ancienne date",
                "Nouvelle date",
                "Modifié par",
                "Modifié le",
                "Note",
                "-",
            ]
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_search_filter()

    def refresh(self) -> None:
        if self._restricted or not hasattr(self, "table"):
            return

        self._history_data = list_payment_history()
        self._apply_search_filter()

    def _apply_search_filter(self) -> None:
        if self._restricted or not hasattr(self, "table"):
            return

        self.table.setRowCount(0)
        query = self._search_text
        for r in self._history_data:
            haystack = " ".join(
                [
                    str(r.get("id", "")),
                    str(r.get("student_name", "")),
                    str(r.get("class_name", "")),
                    str(r.get("action", "")),
                    str(r.get("old_status", "")),
                    str(r.get("new_status", "")),
                    str(r.get("old_amount", "")),
                    str(r.get("new_amount", "")),
                    str(r.get("old_paid_date", "")),
                    str(r.get("new_paid_date", "")),
                    str(r.get("changed_by", "")),
                    str(r.get("changed_at", "")),
                    str(r.get("note", "")),
                ]
            ).lower()
            if query and query not in haystack:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(r.get("student_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(r.get("class_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(r.get("action", "")))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("old_status", "") or ""))
            self.table.setItem(row, 5, QTableWidgetItem(r.get("new_status", "") or ""))
            self.table.setItem(row, 6, QTableWidgetItem(str(r.get("old_amount", "") or "")))
            self.table.setItem(row, 7, QTableWidgetItem(str(r.get("new_amount", "") or "")))
            self.table.setItem(row, 8, QTableWidgetItem(r.get("old_paid_date", "") or ""))
            self.table.setItem(row, 9, QTableWidgetItem(r.get("new_paid_date", "") or ""))
            self.table.setItem(row, 10, QTableWidgetItem(r.get("changed_by", "") or ""))
            self.table.setItem(row, 11, QTableWidgetItem(r.get("changed_at", "") or ""))
            self.table.setItem(row, 12, QTableWidgetItem(r.get("note", "") or ""))
            self.table.setItem(row, 13, QTableWidgetItem(""))

    def _parse_optional_int(self, s: str) -> Optional[int]:
        s = (s or "").strip()
        if not s:
            return None
        return int(s)

    def _parse_optional_float(self, s: str) -> Optional[float]:
        s = (s or "").strip()
        if not s:
            return None
        return float(s)

    def _get_session_user_id(self) -> int:
        # Keep compatibility with older session usage.
        from schoolfin.auth.session import get_session

        session = get_session()
        if not session:
            raise ValueError("Not authenticated")
        return int(session.user_id)

    def _read_form(self) -> dict:
        assert self._history_id_input
        assert self._student_id_input
        assert self._action_input
        assert self._old_status_input
        assert self._new_status_input
        assert self._old_amount_input
        assert self._new_amount_input
        assert self._old_paid_date_input
        assert self._new_paid_date_input
        assert self._note_input

        history_id = self._parse_optional_int(self._history_id_input.text())
        student_id = self._parse_optional_int(self._student_id_input.text())
        action = (self._action_input.text() or "").strip()
        old_status = self._old_status_input.currentData()
        new_status = self._new_status_input.currentData()
        old_amount = self._parse_optional_float(self._old_amount_input.text())
        new_amount = self._parse_optional_float(self._new_amount_input.text())

        old_paid_date = (self._old_paid_date_input.text() or "").strip() or None
        new_paid_date = (self._new_paid_date_input.text() or "").strip() or None
        note = (self._note_input.text() or "").strip()

        return {
            "history_id": history_id,
            "student_id": student_id,
            "action": action,
            "old_status": old_status,
            "new_status": new_status,
            "old_amount": old_amount,
            "new_amount": new_amount,
            "old_paid_date": old_paid_date,
            "new_paid_date": new_paid_date,
            "note": note,
        }

    def on_load(self) -> None:
        try:
            form = self._read_form()
            if form["history_id"] is None:
                QMessageBox.warning(self, "History", "Enter History ID")
                return

            entry = get_payment_history_entry(form["history_id"])
            if not entry:
                QMessageBox.warning(self, "Historique", "Entrée d'historique introuvable")
                return

            # Fill fields
            assert self._history_id_input
            assert self._student_id_input
            assert self._action_input

            self._history_id_input.setText(str(entry.get("id", "")))
            self._student_id_input.setText(str(entry.get("student_id", "")))
            self._action_input.setText(entry.get("action", "") or "")

            # status combos
            assert self._old_status_input
            assert self._new_status_input
            old_status = entry.get("old_status")
            new_status = entry.get("new_status")

            idx_old = self._old_status_input.findData(old_status)
            self._old_status_input.setCurrentIndex(0 if idx_old < 0 else idx_old)

            idx_new = self._new_status_input.findData(new_status)
            self._new_status_input.setCurrentIndex(0 if idx_new < 0 else idx_new)

            # amounts/dates/note
            assert self._old_amount_input
            assert self._new_amount_input
            assert self._old_paid_date_input
            assert self._new_paid_date_input
            assert self._note_input

            self._old_amount_input.setText("" if entry.get("old_amount") is None else str(entry.get("old_amount")))
            self._new_amount_input.setText("" if entry.get("new_amount") is None else str(entry.get("new_amount")))
            self._old_paid_date_input.setText(entry.get("old_paid_date") or "")
            self._new_paid_date_input.setText(entry.get("new_paid_date") or "")
            self._note_input.setText(entry.get("note") or "")

            QMessageBox.information(self, "Historique", "Chargé")
        except Exception as e:
            QMessageBox.critical(self, "History", str(e))

    def on_create(self) -> None:
        try:
            form = self._read_form()
            if form["student_id"] is None:
                QMessageBox.warning(self, "History", "Enter Student ID")
                return
            if not form["action"]:
                QMessageBox.warning(self, "History", "Enter Action")
                return

            changed_by = self._get_session_user_id()

            hid = create_payment_history_entry(
                payment_id=None,
                student_id=int(form["student_id"]),
                action=form["action"],
                old_status=form["old_status"],
                new_status=form["new_status"],
                old_amount=form["old_amount"],
                new_amount=form["new_amount"],
                old_paid_date=form["old_paid_date"],
                new_paid_date=form["new_paid_date"],
                changed_by=changed_by,
                note=form["note"],
            )

            assert self._history_id_input
            self._history_id_input.setText(str(hid))

            QMessageBox.information(self, "Historique", "Créé")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "History", str(e))

    def on_update(self) -> None:
        try:
            form = self._read_form()
            if form["history_id"] is None:
                QMessageBox.warning(self, "History", "Enter History ID")
                return
            if form["student_id"] is None:
                QMessageBox.warning(self, "History", "Enter Student ID")
                return
            if not form["action"]:
                QMessageBox.warning(self, "History", "Enter Action")
                return

            changed_by = self._get_session_user_id()

            update_payment_history_entry(
                int(form["history_id"]),
                payment_id=None,
                student_id=int(form["student_id"]),
                action=form["action"],
                old_status=form["old_status"],
                new_status=form["new_status"],
                old_amount=form["old_amount"],
                new_amount=form["new_amount"],
                old_paid_date=form["old_paid_date"],
                new_paid_date=form["new_paid_date"],
                changed_by=changed_by,
                note=form["note"],
            )

            QMessageBox.information(self, "Historique", "Modifié")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "History", str(e))

    def on_delete(self) -> None:
        try:
            form = self._read_form()
            if form["history_id"] is None:
                QMessageBox.warning(self, "History", "Enter History ID")
                return

            if QMessageBox.question(
                self,
                "Supprimer",
                f"Supprimer l'entrée d'historique ID={form['history_id']} ?",
            ) != QMessageBox.StandardButton.Yes:
                return

            delete_payment_history_entry(int(form["history_id"]))
            QMessageBox.information(self, "Historique", "Supprimé")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "History", str(e))

