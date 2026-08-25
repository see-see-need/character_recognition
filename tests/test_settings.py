from PySide6.QtCore import QSettings

from screen_ocr.core.models import AppSettings, TranslationSettings
from screen_ocr.services.settings import SettingsStore


def test_settings_round_trip(tmp_path) -> None:
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    store = SettingsStore(backend)
    expected = AppSettings(
        hotkey="Ctrl+Alt+Q",
        auto_copy=False,
        start_at_login=True,
        translation=TranslationSettings(auto_translate=True),
    )
    store.save(expected)
    assert store.load() == expected
    assert backend.value("translation/enabled") is None
    assert backend.value("translation/provider") is None
    assert "API" not in (tmp_path / "settings.ini").read_text(encoding="utf-8")


def test_legacy_translation_enabled_migrates_on_save(tmp_path) -> None:
    backend = QSettings(str(tmp_path / "legacy.ini"), QSettings.Format.IniFormat)
    backend.setValue("translation/enabled", True)
    store = SettingsStore(backend)
    loaded = store.load()
    assert loaded.translation.auto_translate is True
    store.save(loaded)
    assert backend.value("translation/enabled") is None
    assert backend.value("translation/auto_translate", type=bool) is True
