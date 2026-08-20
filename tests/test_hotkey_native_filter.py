from __future__ import annotations

import ctypes
from ctypes import wintypes

from screen_ocr.ui.hotkey import HOTKEY_ID, WM_HOTKEY, NativeHotkeyFilter


class FakeQByteArray:
    def __init__(self, value: bytes) -> None:
        self._value = value

    def data(self) -> bytes:
        return self._value


def test_native_filter_accepts_qbytearray_event_names(monkeypatch) -> None:
    monkeypatch.setattr("screen_ocr.ui.hotkey.sys.platform", "win32")
    activations: list[bool] = []
    event_filter = NativeHotkeyFilter(lambda: activations.append(True))
    message = wintypes.MSG()
    message.message = WM_HOTKEY
    message.wParam = HOTKEY_ID

    assert event_filter.nativeEventFilter(
        FakeQByteArray(b"windows_generic_MSG"), ctypes.addressof(message)
    ) is True
    assert activations == [True]


def test_native_filter_accepts_bytes_event_names(monkeypatch) -> None:
    monkeypatch.setattr("screen_ocr.ui.hotkey.sys.platform", "win32")
    activations: list[bool] = []
    event_filter = NativeHotkeyFilter(lambda: activations.append(True))
    message = wintypes.MSG()
    message.message = WM_HOTKEY
    message.wParam = HOTKEY_ID

    assert event_filter.nativeEventFilter(
        b"windows_dispatcher_MSG", ctypes.addressof(message)
    ) is True
    assert activations == [True]
