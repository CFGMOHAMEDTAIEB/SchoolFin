from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QStyle,
)

from schoolfin.auth.session import get_session, set_session
from schoolfin.ui.icon_utils import get_app_icon_path
from schoolfin.ui.pages.classes_page import ClassesPage
from schoolfin.ui.pages.dashboard_page import DashboardPage
from schoolfin.ui.pages.history_page import HistoryPage
from schoolfin.ui.pages.payments_page import PaymentsPage
from schoolfin.ui.pages.print_page import PrintExtractPage
from schoolfin.ui.pages.students_page import StudentsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("SchoolFin • Tableau de bord")
        self.setMinimumSize(1180, 760)

        icon_path = get_app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))

        session = get_session()
        self.role = session.role if session else "financial"
        self.username = session.username if session else "Invité"

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QWidget#MainWindow {
                background: #eef2fb;
            }
            QFrame#Sidebar {
                background: #0d2470;
                border-top-right-radius: 28px;
                border-bottom-right-radius: 28px;
                color: white;
            }
            QFrame#Header {
                background: rgba(255, 255, 255, 0.96);
                border-radius: 24px;
            }
            QFrame#Badge {
                background: rgba(13, 36, 112, 0.08);
                border: 1px solid rgba(13, 36, 112, 0.12);
                border-radius: 14px;
            }
            QLabel#SidebarTitle {
                color: white;
                font-size: 20px;
                font-weight: 800;
            }
            QLabel#SidebarSubtitle {
                color: rgba(255, 255, 255, 0.78);
                font-size: 11px;
                letter-spacing: 0.8px;
                text-transform: uppercase;
            }
            QLabel#HeaderTitle {
                color: #10213a;
                font-size: 26px;
                font-weight: 800;
            }
            QLabel#HeaderSubtitle {
                color: #6b778e;
                font-size: 13px;
            }
            QLabel#ChipText {
                color: #16326f;
                font-weight: 700;
                font-size: 12px;
            }
            QListWidget#NavList {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget#NavList::item {
                color: rgba(255, 255, 255, 0.86);
                padding: 12px 14px;
                margin: 4px 8px;
                border-radius: 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QListWidget#NavList::item:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QListWidget#NavList::item:selected {
                background: rgba(255, 255, 255, 0.16);
                color: white;
            }
            QPushButton#SidebarLogout {
                color: white;
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
                padding: 11px 14px;
                font-weight: 700;
            }
            QPushButton#SidebarLogout:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QLineEdit#GlobalSearch {
                background: white;
                border: 1px solid #d8e0f0;
                border-radius: 12px;
                padding: 10px 12px;
                color: #10213a;
            }
            """
        )

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(22, 22, 22, 22)
        sidebar_layout.setSpacing(18)

        brand = QHBoxLayout()
        brand.setSpacing(12)
        brand_icon = QLabel()
        brand_icon.setFixedSize(48, 48)
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
            """
        )
        brand_icon.setPixmap(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon).pixmap(24, 24)
        )

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        brand_title = QLabel("SchoolFin")
        brand_title.setObjectName("SidebarTitle")
        brand_subtitle = QLabel("Portail administratif")
        brand_subtitle.setObjectName("SidebarSubtitle")
        brand_text.addWidget(brand_title)
        brand_text.addWidget(brand_subtitle)
        brand.addWidget(brand_icon)
        brand.addLayout(brand_text)
        brand.addStretch(1)
        sidebar_layout.addLayout(brand)

        self.menu = QListWidget()
        self.menu.setObjectName("NavList")
        self.menu.setSpacing(2)
        self.menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        sidebar_layout.addWidget(self.menu, 1)

        logout = QPushButton("Déconnexion")
        logout.setObjectName("SidebarLogout")
        logout.setCursor(Qt.CursorShape.PointingHandCursor)
        logout.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(logout)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 18, 22, 18)
        header_layout.setSpacing(14)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        header_title = QLabel(self._header_title())
        header_title.setObjectName("HeaderTitle")
        header_subtitle = QLabel(f"Bienvenue, {self.username}. Votre espace s'adapte à votre profil {self._role_label().lower()}.")
        header_subtitle.setObjectName("HeaderSubtitle")
        header_subtitle.setWordWrap(True)
        title_block.addWidget(header_title)
        title_block.addWidget(header_subtitle)

        header_actions = QHBoxLayout()
        header_actions.setSpacing(10)

        chip = QFrame()
        chip.setObjectName("Badge")
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(12, 8, 12, 8)
        chip_layout.setSpacing(8)
        role_icon = QLabel()
        role_icon.setPixmap(self._role_icon().pixmap(16, 16))
        role_text = QLabel(self._role_label())
        role_text.setObjectName("ChipText")
        chip_layout.addWidget(role_icon)
        chip_layout.addWidget(role_text)

        user_chip = QFrame()
        user_chip.setObjectName("Badge")
        user_chip_layout = QHBoxLayout(user_chip)
        user_chip_layout.setContentsMargins(12, 8, 12, 8)
        user_chip_layout.setSpacing(8)
        user_icon = QLabel()
        user_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon).pixmap(16, 16))
        user_text = QLabel(self.username)
        user_text.setObjectName("ChipText")
        user_chip_layout.addWidget(user_icon)
        user_chip_layout.addWidget(user_text)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("GlobalSearch")
        self.search_input.setPlaceholderText("Rechercher")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)

        header_actions.addWidget(chip)
        header_actions.addWidget(user_chip)

        header_layout.addLayout(title_block, 1)
        header_layout.addWidget(self.search_input, 0)
        header_layout.addLayout(header_actions, 0)

        self.stack = QStackedWidget()

        self.menu_items = self._menu_items_for_role(self.role)
        self.pages = {}
        for key, label, icon in self.menu_items:
            item = QListWidgetItem(icon, label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.menu.addItem(item)

        self.pages = self._build_pages()
        for key, page in self.pages.items():
            self.stack.addWidget(page)

        self.menu.currentItemChanged.connect(self._on_menu_changed)
        self.menu.setCurrentRow(0)

        content_layout.addWidget(header)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)

    def _menu_items_for_role(self, role: str):
        items = [
            ("dashboard", "Tableau de bord", self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon)),
            ("payments", "Paiements", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)),
            ("history", "Historique", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)),
            ("print", "Imprimer l'extrait", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)),
        ]
        if role in {"admin", "financial"}:
            items.insert(1, ("classes", "Classes", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)))
            items.insert(2, ("students", "Élèves", self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        return items

    def _build_pages(self):
        pages = {
            "dashboard": DashboardPage(role=self.role),
            "payments": PaymentsPage(role=self.role),
            "history": HistoryPage(role=self.role),
            "print": PrintExtractPage(role=self.role),
        }
        if self.role in {"admin", "financial"}:
            pages["classes"] = ClassesPage(role=self.role)
            pages["students"] = StudentsPage(role=self.role)
        return pages

    def _on_menu_changed(self, current, previous):
        if not current:
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        page = self.pages.get(key)
        if page is not None:
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass
            self.stack.setCurrentWidget(page)
            self._apply_search_to_current_page()

    def _on_search_text_changed(self, text: str):
        self._apply_search_to_current_page(text)

    def _apply_search_to_current_page(self, text: str | None = None):
        page = self.stack.currentWidget()
        if page is None:
            return
        if hasattr(page, "set_search_text"):
            try:
                page.set_search_text(text if text is not None else self.search_input.text())
            except Exception:
                pass

    def notify_data_changed(self, source: str = ""):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    # keep UI responsive even if one page fails to refresh
                    pass

    def _role_label(self) -> str:
        return "Administrateur" if self.role == "admin" else "Financier"

    def _role_icon(self):
        if self.role == "admin":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        return self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)

    def _header_title(self) -> str:
        return "Tableau de bord Administrateur" if self.role == "admin" else "Suivi Financier"

    def _logout(self):
        from schoolfin.ui.login_window import LoginWindow

        set_session(None)
        self.login = LoginWindow()
        self.login.show()
        self.close()

