from pathlib import Path

from schoolfin.ui.icon_utils import get_app_icon_path


def test_app_icon_asset_exists():
    icon_path = get_app_icon_path()

    assert icon_path is not None
    assert icon_path.exists()
    assert icon_path.name == "schoolfin_icon.svg"
