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
)

from schoolfin.auth.session import get_session
from schoolfin.services.payment_service import list_classes, create_class, update_class, delete_class


class ClassesPage(QWidget):
    def __init__(self, role: str):
        super().__init__()
        self.role = role
        self.selected_class_id: int | None = None
        self._search_text = ""
        self._classes_data = []
        self.selected_class_name: str = ""

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Classes"))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Nombre d'élèves"])

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)

        # Create
        create_form = QVBoxLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Nouveau nom de classe")
        self.btn_add = QPushButton("Ajouter la classe")
        self.btn_add.clicked.connect(self.on_add)
        create_form.addWidget(self.name)
        create_form.addWidget(self.btn_add)

        # Update/Delete (admin only)
        crud_form = QVBoxLayout()
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Nom de classe sélectionnée")
        self.btn_update = QPushButton("Mettre à jour")
        self.btn_update.clicked.connect(self.on_update)

        self.btn_delete = QPushButton("Supprimer la classe sélectionnée")
        self.btn_delete.clicked.connect(self.on_delete)

        crud_form.addWidget(QLabel("Actions administrateur"))
        crud_form.addWidget(self.edit_name)
        crud_form.addWidget(self.btn_update)
        crud_form.addWidget(self.btn_delete)

        if self.role not in {"admin", "financial"}:
            for w in (self.name, self.btn_add, self.edit_name, self.btn_update, self.btn_delete):
                w.setDisabled(True)

        layout.addLayout(create_form)
        layout.addLayout(crud_form)

        self.refresh()

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self._apply_search_filter()

    def refresh(self):
        self._classes_data = list_classes()
        self._apply_search_filter()

    def _apply_search_filter(self):
        self.table.setRowCount(0)
        query = self._search_text
        for r in self._classes_data:
            haystack = " ".join(
                [str(r.get("id", "")), str(r.get("name", "")), str(r.get("student_count", 0))]
            ).lower()
            if query and query not in haystack:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(r.get("student_count", 0))))


    def on_selection_changed(self):
        if self.role not in {"admin", "financial"}:
            return
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.selected_class_id = None
            self.selected_class_name = ""
            self.edit_name.setText("")
            return

        row_idx = selected[0].row()
        id_item = self.table.item(row_idx, 0)
        name_item = self.table.item(row_idx, 1)
        if not id_item or not name_item:
            self.selected_class_id = None
            self.selected_class_name = ""
            self.edit_name.setText("")
            return

        self.selected_class_id = int(id_item.text())
        self.selected_class_name = name_item.text()
        self.edit_name.setText(self.selected_class_name)

    def _require_admin(self) -> bool:
        if self.role not in {"admin", "financial"}:
            QMessageBox.warning(self, "Classes", "Seuls les administrateurs et les financiers peuvent modifier les classes")
            return False
        session = get_session()
        if not session:
            QMessageBox.critical(self, "Classes", "Aucune session active")
            return False
        return True

    def on_add(self):
        if self.role not in {"admin", "financial"}:
            return
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Classes", "Enter class name")
            return
        try:
            create_class(name)
        except Exception as e:
            QMessageBox.critical(self, "Classes", str(e))
            return
        self.name.clear()
        main = self.window()
        if hasattr(main, "notify_data_changed"):
            main.notify_data_changed("classes")
        else:
            self.refresh()

    def on_update(self):
        if not self._require_admin():
            return
        if self.selected_class_id is None:
            QMessageBox.warning(self, "Classes", "Select a class first")
            return
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Classes", "Enter class name")
            return
        try:
            update_class(self.selected_class_id, name)
        except Exception as e:
            QMessageBox.critical(self, "Classes", str(e))
            return

        main = self.window()
        if hasattr(main, "notify_data_changed"):
            main.notify_data_changed("classes")
        else:
            self.refresh()

    def on_delete(self):
        if not self._require_admin():
            return
        if self.selected_class_id is None:
            QMessageBox.warning(self, "Classes", "Select a class first")
            return

        confirm = QMessageBox.question(
            self,
            "Supprimer la classe",
            f"Supprimer la classe '{self.selected_class_name}' ?\nLes élèves de cette classe seront également supprimés.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_class(self.selected_class_id)
        except Exception as e:
            QMessageBox.critical(self, "Classes", str(e))
            return

        self.selected_class_id = None
        self.selected_class_name = ""
        self.edit_name.setText("")

        main = self.window()
        if hasattr(main, "notify_data_changed"):
            main.notify_data_changed("classes")
        else:
            self.refresh()


