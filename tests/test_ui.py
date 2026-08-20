import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from screen_ocr.core.models import AppSettings, DisplayResult
from screen_ocr.ui.windows import MainWindow, ResultDialog, TrayController


def get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_capture_button_emits_request() -> None:
    get_app()
    window = MainWindow(AppSettings())
    calls = []
    window.capture_requested.connect(lambda: calls.append(True))
    window.capture_button.click()
    assert calls == [True]


def test_result_shows_auto_copy_feedback_and_text() -> None:
    get_app()
    dialog = ResultDialog()
    dialog.show_result(DisplayResult("Screen OCR", ocr_elapsed_ms=42), auto_copied=True)
    assert dialog.editor.toPlainText() == "Screen OCR"
    assert "已自动复制" in dialog.meta.text()
    dialog.close()


def test_tray_controller_builds_expected_menu() -> None:
    get_app()
    tray = TrayController()
    labels = [action.text() for action in tray.tray.contextMenu().actions() if action.text()]
    assert labels == ["打开屏幕文字识别", "开始框选", "设置", "退出"]
