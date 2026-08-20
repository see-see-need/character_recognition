from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings

from screen_ocr.core.models import AppSettings, TranslationSettings


ORGANIZATION = "PersonalTools"
APPLICATION = "ScreenOCR"


class SettingsStore:
    def __init__(self, backend: QSettings | None = None) -> None:
        self._settings = backend or QSettings(ORGANIZATION, APPLICATION)

    def load(self) -> AppSettings:
        return AppSettings(
            hotkey=str(self._settings.value("capture/hotkey", "Ctrl+Shift+S")),
            auto_copy=self._as_bool(self._settings.value("result/auto_copy", True)),
            start_at_login=self._as_bool(self._settings.value("startup/enabled", False)),
            translation=TranslationSettings(
                enabled=self._as_bool(self._settings.value("translation/enabled", False)),
                provider=str(self._settings.value("translation/provider", "")),
                target_language=str(
                    self._settings.value("translation/target_language", "zh-Hans")
                ),
            ),
        )

    def save(self, value: AppSettings) -> None:
        self._settings.setValue("capture/hotkey", value.hotkey)
        self._settings.setValue("result/auto_copy", value.auto_copy)
        self._settings.setValue("startup/enabled", value.start_at_login)
        self._settings.setValue("translation/enabled", value.translation.enabled)
        self._settings.setValue("translation/provider", value.translation.provider)
        self._settings.setValue(
            "translation/target_language", value.translation.target_language
        )
        self._settings.sync()

    @staticmethod
    def _as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}


def set_start_at_login(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            executable = Path(sys.executable).resolve()
            command = f'"{executable}"'
            if not getattr(sys, "frozen", False):
                command = f'"{executable}" -m screen_ocr'
            winreg.SetValueEx(key, APPLICATION, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APPLICATION)
            except FileNotFoundError:
                pass

