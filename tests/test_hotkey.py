import pytest
from PySide6.QtCore import Qt

from screen_ocr.ui.hotkey import GlobalHotkey, MOD_CONTROL, MOD_NOREPEAT, MOD_SHIFT


def test_default_hotkey_parses_to_windows_values() -> None:
    modifiers, key = GlobalHotkey.parse("Ctrl+Shift+S")
    assert modifiers == MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT
    assert key == int(Qt.Key.Key_S)


@pytest.mark.parametrize("value", ["S", "Ctrl++", "Ctrl+Shift+Space"])
def test_invalid_hotkeys_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        GlobalHotkey.parse(value)

