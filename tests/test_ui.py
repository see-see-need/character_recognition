import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from screen_ocr.core.models import AppSettings, DisplayResult, TranslationResult
from screen_ocr.ui.windows import MainWindow, ResultDialog, SettingsDialog, TrayController


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


def test_manual_translation_uses_current_edited_text() -> None:
    get_app()
    dialog = ResultDialog()
    requested = []
    dialog.translation_requested.connect(requested.append)
    dialog.show_result(DisplayResult("Hello"))
    assert dialog.translation_panel.isHidden()
    dialog.editor.setPlainText("Hello, world")
    dialog.translate_button.click()
    assert requested == ["Hello, world"]
    assert not dialog.translation_panel.isHidden()
    assert not dialog.translate_button.isEnabled()
    dialog.close()


def test_translation_result_is_editable_and_copyable() -> None:
    app = get_app()
    dialog = ResultDialog()
    dialog.show_result(DisplayResult("Hello"))
    dialog.show_translation(TranslationResult("你好", provider="deepseek", elapsed_ms=20))
    dialog.translation_editor.setPlainText("你好！")
    dialog.copy_translation_button.click()
    assert app.clipboard().text() == "你好！"
    assert dialog.translate_button.text() == "重新翻译"
    dialog.close()


def test_translation_error_keeps_original_and_allows_retry() -> None:
    get_app()
    dialog = ResultDialog()
    dialog.show_result(DisplayResult("Hello"))
    dialog.show_translation(
        TranslationResult(None, provider="deepseek", error="请检查网络")
    )
    assert dialog.editor.toPlainText() == "Hello"
    assert dialog.translate_button.text() == "重试翻译"
    assert dialog.translate_button.isEnabled()
    assert dialog.translation_meta.property("error") is True
    dialog.close()


def test_settings_exposes_auto_translate_and_api_key_changes() -> None:
    get_app()
    dialog = SettingsDialog(AppSettings(), has_api_key=True)
    assert dialog.api_key_status.text() == "API Key 已安全保存"
    dialog.auto_translate.setChecked(True)
    dialog.api_key_edit.setText("sk-secret")
    assert dialog.api_key_status.text() == "新 API Key 将在保存后生效"
    assert dialog.values(AppSettings()).translation.auto_translate is True
    assert dialog.api_key_change() == ("sk-secret", False)
    dialog.delete_api_key.setChecked(True)
    assert dialog.api_key_change() == (None, True)
    dialog.close()


def test_tray_controller_builds_expected_menu() -> None:
    get_app()
    tray = TrayController()
    labels = [action.text() for action in tray.tray.contextMenu().actions() if action.text()]
    assert labels == ["打开屏幕文字识别", "开始框选", "持续翻译", "停止持续翻译", "设置", "退出"]
