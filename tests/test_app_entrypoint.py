import runpy
import sys
import types
from pathlib import Path


def test_app_script_can_bootstrap_package_imports(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "schoolfin" / "app.py"

    for name in list(sys.modules):
        if name == "schoolfin" or name.startswith("schoolfin."):
            sys.modules.pop(name, None)

    class FakeQApplication:
        def __init__(self, *args, **kwargs):
            pass

        def setApplicationName(self, *args, **kwargs):
            pass

        def setStyle(self, *args, **kwargs):
            pass

        def setWindowIcon(self, *args, **kwargs):
            pass

        def exec(self):
            return 0

    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QLocale = type(
        "QLocale",
        (),
        {
            "Language": type("Language", (), {"French": "French"}),
            "Country": type("Country", (), {"France": "France"}),
            "setDefault": staticmethod(lambda *args, **kwargs: None),
        },
    )
    qtcore.QSize = object

    qtgui = types.ModuleType("PyQt6.QtGui")
    qtgui.QIcon = lambda *args, **kwargs: None

    qtwidgets = types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QApplication = FakeQApplication

    monkeypatch.setitem(sys.modules, "PyQt6", types.ModuleType("PyQt6"))
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PyQt6.QtGui", qtgui)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", qtwidgets)

    class FakeLoginWindow:
        def __init__(self, *args, **kwargs):
            pass

        def setWindowIcon(self, *args, **kwargs):
            pass

        def show(self):
            pass

    login_window_module = types.ModuleType("schoolfin.ui.login_window")
    login_window_module.LoginWindow = FakeLoginWindow
    monkeypatch.setitem(sys.modules, "schoolfin.ui.login_window", login_window_module)

    runpy.run_path(str(script_path), run_name="__main__")
