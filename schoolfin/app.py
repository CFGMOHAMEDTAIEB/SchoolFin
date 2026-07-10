import sys
from pathlib import Path

# Allow running either as module (`python -m schoolfin.app`) or directly
# (`python schoolfin/app.py`) without import errors.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PyQt6.QtCore import QLocale, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from schoolfin.ui.icon_utils import get_app_icon_path
from schoolfin.ui.login_window import LoginWindow


def main():
    QLocale.setDefault(QLocale(QLocale.Language.French, QLocale.Country.France))
    app = QApplication(sys.argv)
    app.setApplicationName("SchoolFin")
    app.setStyle("Fusion")

    icon_path = get_app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))

    win = LoginWindow()
    if icon_path is not None:
        win.setWindowIcon(QIcon(str(icon_path)))
    win.show()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

