import pytest
from PySide6.QtCore import Qt
from types import SimpleNamespace

from screen_ocr.ui.hotkey import GlobalHotkey, MOD_CONTROL, MOD_NOREPEAT, MOD_SHIFT


def test_default_hotkey_parses_to_windows_values() -> None:
    modifiers, key = GlobalHotkey.parse("Ctrl+Shift+S")
    assert modifiers == MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT
    assert key == int(Qt.Key.Key_S)


@pytest.mark.parametrize("value", ["S", "Ctrl++", "Ctrl+Shift+Space"])
def test_invalid_hotkeys_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        GlobalHotkey.parse(value)


def test_registering_same_hotkey_does_not_claim_it_twice(monkeypatch) -> None:
    class FakeApp:
        def installNativeEventFilter(self, event_filter):
            self.event_filter = event_filter

    class FakeUser32:
        def __init__(self):
            self.register_calls = 0
            self.unregister_calls = 0

        def RegisterHotKey(self, *args):
            self.register_calls += 1
            return 1

        def UnregisterHotKey(self, *args):
            self.unregister_calls += 1
            return 1

    user32 = FakeUser32()
    monkeypatch.setattr(
        "screen_ocr.ui.hotkey.ctypes.windll", SimpleNamespace(user32=user32)
    )
    hotkey = GlobalHotkey(FakeApp())
    assert hotkey.register("Ctrl+Shift+S") is True
    assert hotkey.register("Ctrl+Shift+S") is True
    assert user32.register_calls == 1
    assert user32.unregister_calls == 0
    hotkey.unregister()
    assert user32.unregister_calls == 1
