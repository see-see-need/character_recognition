from PySide6.QtCore import QSettings

from screen_ocr.core.models import AppSettings
from screen_ocr.services.settings import SettingsStore


def test_settings_round_trip(tmp_path) -> None:
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    store = SettingsStore(backend)
    expected = AppSettings(hotkey="Ctrl+Alt+Q", auto_copy=False, start_at_login=True)
    store.save(expected)
    assert store.load() == expected

