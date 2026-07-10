from __future__ import annotations

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QComboBox,
    QFormLayout,
)

from schoolfin.services.payment_service import (
    create_student,
    format_payment_frequency,
    list_classes,
    list_students_by_class,
)


class StudentsPage(QWidget):
    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self._search_text = ""
        self._students_data = []
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Élèves"))

        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.class_filter)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Classe",
            "Nom",
            "Téléphone",
            "Adresse",
            "Date naissance",
            "Parent",
            "Tél parent",
            "Notes",
            "Fréquence",
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        form = QFormLayout()
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Nom complet de l'élève")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Téléphone (facultatif)")
        self.address = QLineEdit()
        self.address.setPlaceholderText("Adresse complète")
        self.birth_date = QLineEdit()
        self.birth_date.setPlaceholderText("AAAA-MM-JJ")
        self.parent_name = QLineEdit()
        self.parent_name.setPlaceholderText("Nom du parent ou tuteur")
        self.parent_phone = QLineEdit()
        self.parent_phone.setPlaceholderText("Téléphone du parent")
        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Remarques / moyen / transport")

        self.class_create = QComboBox()
        self.payment_frequency = QComboBox()
        self.payment_frequency.addItems(["Mensuel", "Trimestriel", "Annuel"])

        self.btn_add = QPushButton("Ajouter l'élève")
        self.btn_add.clicked.connect(self.on_add)

        form.addRow("Classe", self.class_create)
        form.addRow("Nom", self.full_name)
        form.addRow("Téléphone", self.phone)
        form.addRow("Adresse", self.address)
        form.addRow("Date de naissance", self.birth_date)
        form.addRow("Parent", self.parent_name)
        form.addRow("Téléphone parent", self.parent_phone)
        form.addRow("Notes / moyen", self.notes)
        form.addRow("Fréquence", self.payment_frequency)
        form.addRow("", self.btn_add)

        if self.role not in {"admin", "financial"}:
            for w in (
                self.class_create,
                self.full_name,
                self.phone,
                self.address,
                self.birth_date,
                self.parent_name,
                self.parent_phone,
                self.notes,
                self.payment_frequency,
                self.btn_add,
            ):
                w.setDisabled(True)

        layout.addLayout(form)
        self._reload_class_selectors()
        self.refresh()

    def _reload_class_selectors(self):
        selected_filter = self.class_filter.currentData()
        selected_create = self.class_create.currentData()

        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItem("Toutes les classes", None)
        for c in list_classes():
            self.class_filter.addItem(c["name"], c["id"])
        if selected_filter is not None:
            idx = self.class_filter.findData(selected_filter)
            if idx >= 0:
                self.class_filter.setCurrentIndex(idx)
        self.class_filter.blockSignals(False)

        self.class_create.clear()
        for c in list_classes():
            self.class_create.addItem(c["name"], c["id"])
        if selected_create is not None:
            idx = self.class_create.findData(selected_create)
            if idx >= 0:
                self.class_create.setCurrentIndex(idx)

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_search_filter()

    def refresh(self):
        self._reload_class_selectors()
        class_id = self.class_filter.currentData()
        self._students_data = list_students_by_class(class_id)
        self._apply_search_filter()

    def _apply_search_filter(self):
        self.table.setRowCount(0)
        query = self._search_text
        for r in self._students_data:
            haystack = " ".join(
                [
                    str(r.get("full_name", "")),
                    str(r.get("class_name", "")),
                    str(r.get("phone", "")),
                    str(r.get("address", "")),
                    str(r.get("birth_date", "")),
                    str(r.get("parent_name", "")),
                    str(r.get("parent_phone", "")),
                    str(r.get("notes", "")),
                    str(r.get("payment_method", "")),
                    str(r.get("id", "")),
                ]
            ).lower()
            if query and query not in haystack:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["class_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["full_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(r["phone"] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(r.get("address") or ""))
            self.table.setItem(row, 5, QTableWidgetItem(r.get("birth_date") or ""))
            self.table.setItem(row, 6, QTableWidgetItem(r.get("parent_name") or ""))
            self.table.setItem(row, 7, QTableWidgetItem(r.get("parent_phone") or ""))
            self.table.setItem(row, 8, QTableWidgetItem(r.get("notes") or ""))
            self.table.setItem(row, 9, QTableWidgetItem(format_payment_frequency(r.get("payment_frequency"))))

    def on_add(self):
        if self.role not in {"admin", "financial"}:
            return
        full_name = self.full_name.text().strip()
        if not full_name:
            QMessageBox.warning(self, "Élèves", "Saisissez le nom de l'élève")
            return
        class_id = self.class_create.currentData()
        phone = self.phone.text().strip()
        address = self.address.text().strip()
        birth_date = self.birth_date.text().strip()
        parent_name = self.parent_name.text().strip()
        parent_phone = self.parent_phone.text().strip()
        notes = self.notes.text().strip()
        payment_frequency = self.payment_frequency.currentText()
        try:
            create_student(
                int(class_id),
                full_name,
                phone,
                payment_frequency,
                address=address,
                birth_date=birth_date,
                parent_name=parent_name,
                parent_phone=parent_phone,
                notes=notes,
            )
        except Exception as e:
            QMessageBox.critical(self, "Students", str(e))
            return
        self.full_name.clear()
        self.phone.clear()
        self.address.clear()
        self.birth_date.clear()
        self.parent_name.clear()
        self.parent_phone.clear()
        self.notes.clear()
        main = self.window()
        if hasattr(main, "notify_data_changed"):
            main.notify_data_changed("students")
        else:
            self.refresh()

