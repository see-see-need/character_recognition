from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Qt, Signal
from PySide6.QtGui import QKeySequence


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 0x534F


class NativeHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback) -> None:
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message):  # noqa: N802 - Qt API
        # PySide6 6.10 passes a QByteArray here. Comparing it directly with
        # bytes always fails, so normalize it before checking Windows events.
        event_name = (
            event_type.data() if hasattr(event_type, "data") else bytes(event_type)
        )
        if sys.platform == "win32" and event_name in {
            b"windows_generic_MSG",
            b"windows_dispatcher_MSG",
        }:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._callback()
                return True
        return False


class GlobalHotkey(QObject):
    activated = Signal()
    registration_changed = Signal(bool, str)

    def __init__(self, app) -> None:
        super().__init__()
        self._app = app
        self._registered = False
        self._filter = NativeHotkeyFilter(self.activated.emit)
        app.installNativeEventFilter(self._filter)

    @staticmethod
    def parse(sequence_text: str) -> tuple[int, int]:
        sequence = QKeySequence(sequence_text)
        if sequence.isEmpty() or sequence.count() != 1:
            raise ValueError("快捷键必须包含一个按键组合")
        combination = sequence[0]
        modifiers = combination.keyboardModifiers()
        qt_key = int(combination.key())
        native_modifiers = MOD_NOREPEAT
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            native_modifiers |= MOD_CONTROL
        if modifiers & Qt.KeyboardModifier.AltModifier:
            native_modifiers |= MOD_ALT
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            native_modifiers |= MOD_SHIFT
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            native_modifiers |= MOD_WIN
        if native_modifiers == MOD_NOREPEAT:
            raise ValueError("快捷键必须包含 Ctrl、Alt、Shift 或 Win")
        if Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z or Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
            virtual_key = qt_key
        elif Qt.Key.Key_F1 <= qt_key <= Qt.Key.Key_F24:
            virtual_key = 0x70 + qt_key - int(Qt.Key.Key_F1)
        else:
            raise ValueError("请使用字母、数字或 F1–F24 作为主键")
        return native_modifiers, virtual_key

    def register(self, sequence_text: str) -> bool:
        self.unregister()
        if sys.platform != "win32":
            self.registration_changed.emit(False, "全局快捷键仅支持 Windows")
            return False
        try:
            modifiers, virtual_key = self.parse(sequence_text)
        except ValueError as exc:
            self.registration_changed.emit(False, str(exc))
            return False
        ok = bool(ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, modifiers, virtual_key))
        self._registered = ok
        message = "快捷键可用" if ok else "快捷键已被其他程序占用，请更换"
        self.registration_changed.emit(ok, message)
        return ok

    def unregister(self) -> None:
        if self._registered and sys.platform == "win32":
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        self._registered = False
