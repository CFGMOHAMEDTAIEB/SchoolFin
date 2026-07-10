from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from schoolfin.auth.auth_service import authenticate
from schoolfin.auth.session import set_session
from schoolfin.db.db import app_db_path, init_db
from schoolfin.ui.icon_utils import get_app_icon_path
from schoolfin.ui.main_window import MainWindow


class LoginWindow(QWidget):
    ROLE_LABELS = {
        "admin": "Administrateur",
        "financial": "Financier",
    }

    ROLE_SUBTITLES = {
        "admin": "Gestion complète des élèves, classes et paramètres.",
        "financial": "Paiements, suivi des encaissements et rapports financiers.",
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("LoginWindow")
        self.setWindowTitle("SchoolFin • Connexion")
        self.setMinimumSize(1040, 660)

        icon_path = get_app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))

        self._selected_role = "admin"
        self.role_buttons: dict[str, QToolButton] = {}

        self._build_ui()
        init_db()
        print(f"[SchoolFin] Active DB: {app_db_path()}")

    def _build_ui(self):
        self.setStyleSheet(
            """
            QWidget#LoginWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f5f8ff, stop: 0.5 #eef4ff, stop: 1 #f8f9fc);
            }
            QFrame#BrandPanel {
                border-radius: 28px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #102a6a, stop: 1 #1f4ed8);
                color: white;
            }
            QFrame#FormCard {
                border-radius: 28px;
                background: rgba(255, 255, 255, 0.95);
            }
            QLabel#BrandTitle {
                color: white;
                font-size: 32px;
                font-weight: 800;
            }
            QLabel#BrandSubtitle {
                color: rgba(255, 255, 255, 0.88);
                font-size: 14px;
                line-height: 1.4;
            }
            QLabel#SectionLabel {
                color: #274060;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.6px;
                text-transform: uppercase;
            }
            QLabel#FormTitle {
                color: #10213a;
                font-size: 27px;
                font-weight: 800;
            }
            QLabel#FormSubtitle {
                color: #6d7688;
                font-size: 13px;
            }
            QFrame#RoleCard {
                background: #ffffff;
                border: 1px solid #d9e2f2;
                border-radius: 18px;
            }
            QToolButton#RoleButton {
                background: #f7f9ff;
                color: #21314d;
                border: 1px solid #d4def2;
                border-radius: 16px;
                padding: 18px 14px;
                font-size: 15px;
                font-weight: 700;
            }
            QToolButton#RoleButton:hover {
                background: #eef4ff;
            }
            QToolButton#RoleButton:checked {
                background: #102a6a;
                color: white;
                border-color: #102a6a;
            }
            QLabel#RoleHint {
                color: #64728f;
                font-size: 12px;
            }
            QFrame#FieldBox {
                border: 1px solid #d6deef;
                border-radius: 16px;
                background: #f9fbff;
            }
            QFrame#FieldBox:focus-within {
                border: 1px solid #3d68ff;
                background: #ffffff;
            }
            QLabel#FieldLabel {
                color: #35506d;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#FieldIcon {
                color: #8e9db8;
            }
            QLineEdit#FieldEdit {
                background: transparent;
                border: none;
                color: #10213a;
                font-size: 14px;
                padding: 8px 4px;
                selection-background-color: #102a6a;
            }
            QLineEdit#FieldEdit::placeholder {
                color: #9aa6bc;
            }
            QPushButton#LoginButton {
                background: #102a6a;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 14px 18px;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton#LoginButton:hover {
                background: #16379a;
            }
            QPushButton#LoginButton:pressed {
                background: #0d2359;
            }
            QLabel#FooterHint {
                color: #7a879d;
                font-size: 11px;
            }
            """
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(24)

        brand_panel = QFrame()
        brand_panel.setObjectName("BrandPanel")
        brand_panel.setMinimumWidth(360)
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setContentsMargins(30, 30, 30, 30)
        brand_layout.setSpacing(18)

        logo_row = QHBoxLayout()
        logo_badge = QLabel()
        logo_badge.setFixedSize(74, 74)
        logo_badge.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 20px;
            }
            """
        )
        logo_icon = QLabel()
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setPixmap(
            self.style()
            .standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            .pixmap(34, 34)
        )
        logo_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        logo_badge_layout = QVBoxLayout(logo_badge)
        logo_badge_layout.setContentsMargins(0, 0, 0, 0)
        logo_badge_layout.addWidget(logo_icon)
        logo_row.addWidget(logo_badge, 0, Qt.AlignmentFlag.AlignLeft)
        logo_row.addStretch(1)

        brand_title = QLabel("SchoolFin")
        brand_title.setObjectName("BrandTitle")
        brand_subtitle = QLabel(
            "Un espace d’administration scolaire moderne, clair et rapide pour gérer les rôles, les élèves et les paiements."
        )
        brand_subtitle.setObjectName("BrandSubtitle")
        brand_subtitle.setWordWrap(True)

        brand_layout.addLayout(logo_row)
        brand_layout.addSpacing(8)
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_subtitle)
        brand_layout.addSpacing(14)

        brand_layout.addWidget(self._feature_row(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton),
            "Connexion par profil",
            "Choisissez Administrateur ou Financier avant de vous connecter.",
        ))
        brand_layout.addWidget(self._feature_row(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView),
            "Interface modernisée",
            "Cartes, ombres douces et champs plus lisibles pour un meilleur confort visuel.",
        ))
        brand_layout.addWidget(self._feature_row(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "Accès ciblé",
            "Les menus et actions s’adaptent au profil connecté.",
        ))
        brand_layout.addStretch(1)

        support_note = QLabel("Sécurisé pour les équipes administratives et financières.")
        support_note.setObjectName("BrandSubtitle")
        support_note.setWordWrap(True)
        brand_layout.addWidget(support_note)

        form_card = QFrame()
        form_card.setObjectName("FormCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 12)
        shadow.setColor(Qt.GlobalColor.black)
        form_card.setGraphicsEffect(shadow)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(34, 34, 34, 34)
        form_layout.setSpacing(18)

        section_label = QLabel("Accès au portail")
        section_label.setObjectName("SectionLabel")
        form_title = QLabel("Bienvenue sur SchoolFin")
        form_title.setObjectName("FormTitle")
        form_subtitle = QLabel("Sélectionnez votre rôle puis saisissez vos identifiants pour accéder à votre espace.")
        form_subtitle.setObjectName("FormSubtitle")
        form_subtitle.setWordWrap(True)

        form_layout.addWidget(section_label)
        form_layout.addWidget(form_title)
        form_layout.addWidget(form_subtitle)

        role_label = QLabel("Choisir un profil")
        role_label.setObjectName("FieldLabel")
        form_layout.addWidget(role_label)

        role_cards = QHBoxLayout()
        role_cards.setSpacing(12)
        self.role_group = QButtonGroup(self)
        self.role_group.setExclusive(True)

        role_cards.addWidget(
            self._build_role_card(
                role_key="admin",
                title="Administrateur",
                subtitle=self.ROLE_SUBTITLES["admin"],
                icon=self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon),
            )
        )
        role_cards.addWidget(
            self._build_role_card(
                role_key="financial",
                title="Financier",
                subtitle=self.ROLE_SUBTITLES["financial"],
                icon=self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            )
        )
        form_layout.addLayout(role_cards)

        username_widget, self.username = self._build_field(
            "Utilisateur ou email",
            "nom.utilisateur",
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder),
        )
        password_widget, self.password = self._build_field(
            "Mot de passe",
            "••••••••",
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion),
            secret=True,
        )
        self.username.returnPressed.connect(self.on_login)
        self.password.returnPressed.connect(self.on_login)

        form_layout.addWidget(username_widget)
        form_layout.addWidget(password_widget)

        self.btn = QPushButton("Se connecter")
        self.btn.setObjectName("LoginButton")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton))
        self.btn.setIconSize(QSize(18, 18))
        self.btn.clicked.connect(self.on_login)
        form_layout.addWidget(self.btn)

        footer = QLabel("Les menus, statistiques et actions s’ouvrent selon le rôle sélectionné.")
        footer.setObjectName("FooterHint")
        footer.setWordWrap(True)
        form_layout.addWidget(footer)
        form_layout.addStretch(1)

        root.addWidget(brand_panel, 1)
        root.addWidget(form_card, 1)

        self._select_role(self._selected_role)

    def _feature_row(self, icon, title: str, subtitle: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon_box = QLabel()
        icon_box.setFixedSize(42, 42)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
            }
            """
        )
        icon_box.setPixmap(icon.pixmap(22, 22))

        texts = QVBoxLayout()
        texts.setContentsMargins(0, 0, 0, 0)
        texts.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: 700; font-size: 14px;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.84); font-size: 12px;")
        subtitle_label.setWordWrap(True)
        texts.addWidget(title_label)
        texts.addWidget(subtitle_label)

        layout.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(texts)
        return widget

    def _build_role_card(self, role_key: str, title: str, subtitle: str, icon) -> QFrame:
        card = QFrame()
        card.setObjectName("RoleCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        button = QToolButton()
        button.setObjectName("RoleButton")
        button.setCheckable(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setIcon(icon)
        button.setIconSize(QSize(28, 28))
        button.setText(title)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False, key=role_key: self._select_role(key))

        hint = QLabel(subtitle)
        hint.setObjectName("RoleHint")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(button)
        card_layout.addWidget(hint)
        self.role_group.addButton(button)
        self.role_buttons[role_key] = button
        return card

    def _build_field(self, label_text: str, placeholder: str, icon, secret: bool = False) -> tuple[QWidget, QLineEdit]:
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("FieldLabel")

        field_box = QFrame()
        field_box.setObjectName("FieldBox")
        field_layout = QHBoxLayout(field_box)
        field_layout.setContentsMargins(14, 10, 14, 10)
        field_layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setObjectName("FieldIcon")
        icon_label.setFixedWidth(18)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(icon.pixmap(16, 16))

        line_edit = QLineEdit()
        line_edit.setObjectName("FieldEdit")
        line_edit.setPlaceholderText(placeholder)
        if secret:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        field_layout.addWidget(icon_label)
        field_layout.addWidget(line_edit)
        outer.addWidget(label)
        outer.addWidget(field_box)
        return container, line_edit

    def _select_role(self, role_key: str):
        self._selected_role = role_key
        for key, button in self.role_buttons.items():
            button.setChecked(key == role_key)

    def _selected_role_label(self) -> str:
        return self.ROLE_LABELS.get(self._selected_role, self._selected_role)

    def on_login(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Connexion", "Veuillez saisir votre identifiant et votre mot de passe.")
            return

        session = authenticate(username, password, role=self._selected_role)
        if not session:
            QMessageBox.critical(
                self,
                "Connexion",
                f"Identifiants invalides pour le profil {self._selected_role_label().lower()}.",
            )
            return

        set_session(session)
        self.main = MainWindow()
        self.main.show()
        self.close()

