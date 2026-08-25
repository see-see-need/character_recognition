from __future__ import annotations

import ctypes
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QCursor, QFont, QImage
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from screen_ocr.core.models import AppSettings, CaptureRegion, DisplayResult, ProcessingStatus
from screen_ocr.core.translation import TextPipeline
from screen_ocr.services.credentials import WindowsCredentialStore
from screen_ocr.services.ocr_engine import PaddleOcrEngine
from screen_ocr.services.settings import SettingsStore, set_start_at_login
from screen_ocr.services.translation import TranslationService
from screen_ocr.ui.hotkey import GlobalHotkey
from screen_ocr.ui.style import APP_STYLE
from screen_ocr.ui.windows import (
    CaptureOverlay,
    MainWindow,
    ResultDialog,
    SettingsDialog,
    TrayController,
    make_app_icon,
)


SINGLE_INSTANCE_NAME = "PersonalTools.ScreenOCR.SingleInstance"
_ERROR_ALREADY_EXISTS = 183


class SingleInstanceGuard(QObject):
    activation_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._receive_activation)
        self._mutex_handle = None
        self._kernel32 = None
        if sys.platform == "win32":
            self._kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
            self._kernel32.CreateMutexW.argtypes = [
                ctypes.c_void_p,
                ctypes.c_bool,
                ctypes.c_wchar_p,
            ]
            self._kernel32.CreateMutexW.restype = ctypes.c_void_p
            self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            self._kernel32.CloseHandle.restype = ctypes.c_bool

    def start_primary(self) -> bool:
        if self._kernel32 is not None:
            handle = self._kernel32.CreateMutexW(
                None, False, f"Local\\{SINGLE_INSTANCE_NAME}.Mutex"
            )
            if not handle:
                return False
            if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
                self._kernel32.CloseHandle(handle)
                self.notify_primary()
                return False
            self._mutex_handle = handle

        if not self._server.listen(SINGLE_INSTANCE_NAME):
            QLocalServer.removeServer(SINGLE_INSTANCE_NAME)
            if not self._server.listen(SINGLE_INSTANCE_NAME):
                self.close()
                return False
        return True

    @staticmethod
    def notify_primary() -> bool:
        socket = QLocalSocket()
        socket.connectToServer(SINGLE_INSTANCE_NAME)
        if not socket.waitForConnected(500):
            return False
        socket.write(b"show")
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True

    def _receive_activation(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            socket.readAll()
            socket.disconnectFromServer()
            socket.deleteLater()
        self.activation_requested.emit()

    def close(self) -> None:
        self._server.close()
        if self._mutex_handle is not None and self._kernel32 is not None:
            self._kernel32.CloseHandle(self._mutex_handle)
            self._mutex_handle = None


class OcrWorker(QObject):
    completed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._engine = PaddleOcrEngine()

    @Slot(object)
    def recognize(self, region: CaptureRegion) -> None:
        image = region.image.convertToFormat(QImage.Format.Format_RGBA8888)
        buffer = image.constBits()
        rgba = np.frombuffer(buffer, dtype=np.uint8, count=image.sizeInBytes()).reshape(
            image.height(), image.width(), 4
        )
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        self.completed.emit(self._engine.recognize(bgr))


class OcrService(QObject):
    request = Signal(object)
    completed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.busy = False
        self._thread = QThread(self)
        self._worker = OcrWorker()
        self._worker.moveToThread(self._thread)
        self.request.connect(self._worker.recognize)
        self._worker.completed.connect(self._on_completed)
        self._thread.start()

    def submit(self, region: CaptureRegion) -> bool:
        if self.busy:
            return False
        self.busy = True
        self.request.emit(region)
        return True

    @Slot(object)
    def _on_completed(self, result) -> None:
        self.busy = False
        self.completed.emit(result)

    def shutdown(self) -> None:
        self._thread.quit()
        self._thread.wait()


class CaptureService(QObject):
    selected = Signal(object)
    cancelled = Signal()

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._overlay: CaptureOverlay | None = None

    def begin(self) -> None:
        if self._overlay is not None:
            return
        screen = self._app.screenAt(QCursor.pos()) or self._app.primaryScreen()
        if screen is None:
            self.cancelled.emit()
            return
        screenshot = screen.grabWindow(0)
        self._overlay = CaptureOverlay(screen, screenshot)
        self._overlay.selected.connect(self._selected)
        self._overlay.cancelled.connect(self._cancelled)
        self._overlay.show()

    @Slot(object)
    def _selected(self, region: CaptureRegion) -> None:
        self._overlay = None
        self.selected.emit(region)

    def _cancelled(self) -> None:
        self._overlay = None
        self.cancelled.emit()


class ResultPresenter(QObject):
    def __init__(self, app: QApplication, dialog: ResultDialog) -> None:
        super().__init__()
        self._app = app
        self._dialog = dialog

    def present(self, result: DisplayResult, settings: AppSettings) -> None:
        copied = settings.auto_copy and bool(result.original_text)
        if copied:
            self._app.clipboard().setText(result.original_text)
        self._dialog.show_result(result, auto_copied=copied)


class ApplicationController(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.pipeline = TextPipeline()
        self.credentials = WindowsCredentialStore()
        self.main = MainWindow(self.settings)
        self.result = ResultDialog(self.main)
        self.presenter = ResultPresenter(app, self.result)
        self.capture = CaptureService(app)
        self.ocr = OcrService()
        self.translation = TranslationService(self.credentials)
        self.hotkey = GlobalHotkey(app)
        self.tray = TrayController(self.main)
        self._restore_main_after_capture = False
        self._restore_result_after_capture = False
        self._quit_after_ocr = False

        self.main.capture_requested.connect(self.start_capture)
        self.main.settings_requested.connect(self.open_settings)
        self.main.quit_requested.connect(self.quit)
        self.result.recapture_requested.connect(self.start_capture)
        self.result.translation_requested.connect(self._translate)
        self.capture.selected.connect(self._recognize)
        self.capture.cancelled.connect(self._capture_cancelled)
        self.ocr.completed.connect(self._ocr_completed)
        self.translation.completed.connect(self.result.show_translation)
        self.hotkey.activated.connect(self.start_capture)
        self.hotkey.registration_changed.connect(self._hotkey_status)
        self.tray.show_requested.connect(self.show_main)
        self.tray.capture_requested.connect(self.start_capture)
        self.tray.settings_requested.connect(self.open_settings)
        self.tray.quit_requested.connect(self.quit)
        self.app.aboutToQuit.connect(self.ocr.shutdown)
        self.app.aboutToQuit.connect(self.translation.shutdown)

    def start(self) -> None:
        self.tray.show()
        self.hotkey.register(self.settings.hotkey)
        self.main.show()

    def show_main(self) -> None:
        self.main.show()
        self.main.raise_()
        self.main.activateWindow()

    @Slot()
    def start_capture(self) -> None:
        if self.ocr.busy:
            self.tray.notify("正在识别", "请等待本次识别完成")
            return
        self.translation.invalidate()
        self._restore_main_after_capture = self.main.isVisible()
        self._restore_result_after_capture = self.result.isVisible()
        self.main.hide()
        self.result.hide()
        QTimer.singleShot(160, self.capture.begin)

    @Slot(object)
    def _recognize(self, region: CaptureRegion) -> None:
        self.main.set_processing(True, "正在本机识别，首次使用需要加载模型…")
        self.show_main()
        if not self.ocr.submit(region):
            self.main.set_processing(False, "已有识别任务正在运行")

    def _capture_cancelled(self) -> None:
        self.main.set_processing(False, "已取消框选")
        if self._restore_main_after_capture:
            self.show_main()
        if self._restore_result_after_capture:
            self.result.show()
            self.result.raise_()

    @Slot(object)
    def _ocr_completed(self, ocr_result) -> None:
        self.translation.invalidate()
        display = self.pipeline.without_translation(ocr_result)
        self.main.set_processing(False, "识别完成" if ocr_result.text else "未识别到文字")
        self.presenter.present(display, self.settings)
        if self.settings.translation.auto_translate and ocr_result.text:
            self.result.request_translation()
        if ocr_result.status == ProcessingStatus.ERROR:
            self.tray.notify("识别失败", ocr_result.error or "请重试")
        if self._quit_after_ocr:
            QTimer.singleShot(0, self.quit)

    @Slot(str)
    def _translate(self, text: str) -> None:
        self.translation.submit(text)

    def open_settings(self) -> None:
        try:
            has_api_key = bool(self.credentials.get("deepseek"))
        except OSError:
            has_api_key = False
        dialog = SettingsDialog(self.settings, has_api_key, self.main)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        updated = dialog.values(self.settings)
        if not updated.hotkey:
            QMessageBox.warning(self.main, "快捷键无效", "请设置一个包含修饰键的快捷键。")
            return
        try:
            GlobalHotkey.parse(updated.hotkey)
        except ValueError as exc:
            QMessageBox.warning(self.main, "快捷键无效", str(exc))
            return
        hotkey_changed = updated.hotkey != self.settings.hotkey
        if hotkey_changed and not self.hotkey.register(updated.hotkey):
            self.hotkey.register(self.settings.hotkey)
            QMessageBox.warning(
                self.main,
                "快捷键不可用",
                "这个快捷键已被其他程序占用。原快捷键仍然有效。",
            )
            return
        api_key, delete_api_key = dialog.api_key_change()
        try:
            if delete_api_key:
                self.credentials.delete("deepseek")
            elif api_key is not None:
                self.credentials.set("deepseek", api_key)
                if self.credentials.get("deepseek") != api_key:
                    raise OSError("保存后回读校验失败")
        except (OSError, ValueError) as exc:
            if hotkey_changed:
                self.hotkey.register(self.settings.hotkey)
            QMessageBox.warning(
                self.main,
                "无法保存 API Key",
                f"Windows 凭据管理器返回错误：{exc}",
            )
            return
        if updated.start_at_login != self.settings.start_at_login:
            try:
                set_start_at_login(updated.start_at_login)
            except OSError as exc:
                QMessageBox.warning(self.main, "无法修改开机启动", str(exc))
                updated = AppSettings(
                    hotkey=updated.hotkey,
                    auto_copy=updated.auto_copy,
                    start_at_login=self.settings.start_at_login,
                    translation=updated.translation,
                )
        self.settings = updated
        self.store.save(updated)
        self.main.update_shortcut(updated.hotkey)
        self.main.status_label.setText("设置已保存")

    def _hotkey_status(self, ok: bool, message: str) -> None:
        self.main.status_label.setText(message)

    def quit(self) -> None:
        if self.ocr.busy:
            self._quit_after_ocr = True
            self.main.status_label.setText("识别完成后将自动退出")
            self.tray.notify("正在完成识别", "为安全释放 OCR 线程，完成后将自动退出")
            return
        self.hotkey.unregister()
        self.main.force_close()
        self.app.quit()


def windows_high_contrast_enabled() -> bool:
    if sys.platform != "win32":
        return False

    class HIGHCONTRAST(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("dwFlags", ctypes.c_uint),
            ("lpszDefaultScheme", ctypes.c_wchar_p),
        ]

    value = HIGHCONTRAST(ctypes.sizeof(HIGHCONTRAST), 0, None)
    ok = ctypes.windll.user32.SystemParametersInfoW(0x0042, value.cbSize, ctypes.byref(value), 0)
    return bool(ok and value.dwFlags & 0x00000001)


def create_application(
    argv: list[str] | None = None,
) -> tuple[QApplication, ApplicationController | None]:
    app = QApplication(argv or sys.argv)
    app.setApplicationName("屏幕文字识别")
    app.setOrganizationName("PersonalTools")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(make_app_icon())
    app.setFont(QFont("Microsoft YaHei UI", 10))
    if not windows_high_contrast_enabled():
        app.setStyle("Fusion")
        app.setStyleSheet(APP_STYLE)
    single_instance = SingleInstanceGuard(app)
    if not single_instance.start_primary():
        return app, None
    controller = ApplicationController(app)
    single_instance.activation_requested.connect(controller.show_main)
    app.aboutToQuit.connect(single_instance.close)
    controller.single_instance = single_instance
    return app, controller


def run_ocr_diagnostic(output_path: str) -> int:
    """Exercise the bundled predictor without opening the desktop interface."""
    payload: dict[str, object]
    try:
        image = np.full((220, 900, 3), 255, dtype=np.uint8)
        cv2.putText(
            image,
            "Screen OCR Test 12345",
            (28, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.7,
            (15, 23, 42),
            3,
            cv2.LINE_AA,
        )
        result = PaddleOcrEngine().recognize(image)
        payload = {
            "ok": bool(result.text) and not result.error,
            "text": result.text,
            "line_count": len(result.lines),
            "elapsed_ms": result.elapsed_ms,
            "error": result.error,
        }
    except Exception as exc:  # pragma: no cover - protects frozen diagnostics
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    Path(output_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if payload["ok"] else 1


def run() -> int:
    if "--diagnose-ocr" in sys.argv:
        argument_index = sys.argv.index("--diagnose-ocr")
        try:
            output_path = sys.argv[argument_index + 1]
        except IndexError:
            return 2
        return run_ocr_diagnostic(output_path)
    app, controller = create_application()
    if controller is None:
        return 0
    controller.start()
    return app.exec()
