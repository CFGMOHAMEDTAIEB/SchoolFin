import sys
from pathlib import Path
from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QApplication

# Allow running either as module (`python -m schoolfin.app`) or directly
# (`python schoolfin/app.py`) without import errors.
if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from schoolfin.ui.login_window import LoginWindow


def main():
    QLocale.setDefault(QLocale(QLocale.Language.French, QLocale.Country.France))
    app = QApplication(sys.argv)
    app.setApplicationName("SchoolFin")
    app.setStyle("Fusion")
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

