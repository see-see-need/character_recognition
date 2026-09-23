from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QCloseEvent, QFont, QIcon, QImage, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QKeySequenceEdit,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from screen_ocr.core.models import (
    AppSettings,
    CaptureRegion,
    DisplayResult,
    Rect,
    TranslationResult,
    TranslationSettings,
)


def make_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#2563EB"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRect(4, 4, 56, 56), 14, 14)
    painter.setPen(QPen(QColor("white"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(18, 20, 46, 20)
    painter.drawLine(32, 20, 32, 45)
    painter.drawLine(23, 45, 41, 45)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    capture_requested = Signal()
    live_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._allow_close = False
        self.setWindowTitle("屏幕文字识别")
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(460, 420)
        self.resize(520, 450)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 30, 32, 28)
        layout.setSpacing(18)

        title = QLabel("框选屏幕，提取文字")
        title.setObjectName("title")
        subtitle = QLabel("截图只在本机处理。支持简中、繁中、英文、日文和韩文。")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        self.capture_button = QPushButton("开始框选")
        self.capture_button.setObjectName("primaryButton")
        self.capture_button.setMinimumHeight(52)
        self.capture_button.clicked.connect(self.capture_requested)
        self.live_button = QPushButton("持续翻译")
        self.live_button.setMinimumHeight(44)
        self.live_button.clicked.connect(self.live_requested)

        shortcut_frame = QFrame()
        shortcut_frame.setObjectName("infoPanel")
        shortcut_layout = QHBoxLayout(shortcut_frame)
        shortcut_layout.setContentsMargins(16, 13, 16, 13)
        shortcut_label = QLabel("全局快捷键")
        self.shortcut_value = QLabel(settings.hotkey)
        self.shortcut_value.setObjectName("shortcutValue")
        shortcut_layout.addWidget(shortcut_label)
        shortcut_layout.addStretch()
        shortcut_layout.addWidget(self.shortcut_value)

        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)

        settings_button = QPushButton("设置")
        settings_button.clicked.connect(self.settings_requested)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(4)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.live_button)
        layout.addWidget(shortcut_frame)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.setCentralWidget(body)

    def set_processing(self, processing: bool, message: str) -> None:
        self.capture_button.setDisabled(processing)
        self.live_button.setDisabled(processing)
        self.capture_button.setText("正在识别…" if processing else "开始框选")
        self.status_label.setText(message)

    def update_shortcut(self, value: str) -> None:
        self.shortcut_value.setText(value)

    def force_close(self) -> None:
        self._allow_close = True
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._allow_close:
            event.accept()
        else:
            event.ignore()
            self.hide()


class SettingsDialog(QDialog):
    def __init__(
        self, settings: AppSettings, has_api_key: bool = False, parent=None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        hotkey_label = QLabel("全局截图快捷键")
        hotkey_label.setObjectName("fieldLabel")
        self.hotkey_edit = QKeySequenceEdit(QKeySequence(settings.hotkey))
        self.hotkey_edit.setMaximumSequenceLength(1)
        self.auto_copy = QCheckBox("识别完成后自动复制")
        self.auto_copy.setChecked(settings.auto_copy)
        self.startup = QCheckBox("登录 Windows 后自动启动")
        self.startup.setChecked(settings.start_at_login)
        self.auto_translate = QCheckBox("识别后自动翻译为简体中文")
        self.auto_translate.setChecked(settings.translation.auto_translate)

        api_key_label = QLabel("DeepSeek API Key")
        api_key_label.setObjectName("fieldLabel")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setClearButtonEnabled(True)
        if has_api_key:
            self.api_key_edit.setPlaceholderText("已安全保存；留空则保持不变")
        else:
            self.api_key_edit.setPlaceholderText("请输入 DeepSeek API Key")
        self.delete_api_key = QCheckBox("删除已保存的 API Key")
        self.delete_api_key.setVisible(has_api_key)
        self.delete_api_key.toggled.connect(self.api_key_edit.setDisabled)
        self.api_key_status = QLabel(
            "API Key 已安全保存" if has_api_key else "尚未配置 API Key"
        )
        self.api_key_status.setObjectName(
            "successHint" if has_api_key else "hint"
        )
        self.api_key_edit.textChanged.connect(self._api_key_text_changed)

        note = QLabel(
            "翻译时只会把识别文字发送到 DeepSeek，不会上传截图。"
            "API Key 保存在 Windows 凭据管理器中。"
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(hotkey_label)
        layout.addWidget(self.hotkey_edit)
        layout.addSpacing(4)
        layout.addWidget(self.auto_copy)
        layout.addWidget(self.startup)
        layout.addSpacing(4)
        layout.addWidget(self.auto_translate)
        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_edit)
        layout.addWidget(self.api_key_status)
        layout.addWidget(self.delete_api_key)
        layout.addWidget(note)
        layout.addSpacing(8)
        layout.addWidget(buttons)

    def values(self, previous: AppSettings) -> AppSettings:
        return AppSettings(
            hotkey=self.hotkey_edit.keySequence().toString(
                QKeySequence.SequenceFormat.PortableText
            ),
            auto_copy=self.auto_copy.isChecked(),
            start_at_login=self.startup.isChecked(),
            translation=TranslationSettings(
                auto_translate=self.auto_translate.isChecked(),
                provider="deepseek",
                target_language="zh-Hans",
            ),
        )

    def api_key_change(self) -> tuple[str | None, bool]:
        if not self.delete_api_key.isHidden() and self.delete_api_key.isChecked():
            return None, True
        value = self.api_key_edit.text().strip()
        return (value or None), False

    def _api_key_text_changed(self, value: str) -> None:
        if value.strip():
            self.api_key_status.setText("新 API Key 将在保存后生效")
            self.api_key_status.setObjectName("hint")
            self.api_key_status.style().unpolish(self.api_key_status)
            self.api_key_status.style().polish(self.api_key_status)


class ResultDialog(QDialog):
    recapture_requested = Signal()
    translation_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("识别结果")
        self.setWindowIcon(make_app_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.resize(680, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        heading = QLabel("识别结果")
        heading.setObjectName("dialogTitle")
        self.meta = QLabel("")
        self.meta.setObjectName("hint")
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("没有可显示的文字")
        self.editor.setAcceptRichText(False)

        self.translation_panel = QFrame()
        self.translation_panel.setObjectName("translationPanel")
        translation_layout = QVBoxLayout(self.translation_panel)
        translation_layout.setContentsMargins(14, 12, 14, 14)
        translation_layout.setSpacing(9)
        translation_header = QHBoxLayout()
        translation_title = QLabel("简体中文翻译")
        translation_title.setObjectName("fieldLabel")
        self.copy_translation_button = QPushButton("复制译文")
        self.copy_translation_button.clicked.connect(self.copy_translation)
        self.copy_translation_button.setEnabled(False)
        translation_header.addWidget(translation_title)
        translation_header.addStretch()
        translation_header.addWidget(self.copy_translation_button)
        self.translation_meta = QLabel("")
        self.translation_meta.setObjectName("hint")
        self.translation_meta.setWordWrap(True)
        self.translation_editor = QTextEdit()
        self.translation_editor.setAcceptRichText(False)
        self.translation_editor.setPlaceholderText("译文会显示在这里")
        translation_layout.addLayout(translation_header)
        translation_layout.addWidget(self.translation_meta)
        translation_layout.addWidget(self.translation_editor, 1)
        self.translation_panel.hide()

        actions = QHBoxLayout()
        self.recapture = QPushButton("重新框选")
        self.recapture.clicked.connect(self.recapture_requested)
        self.translate_button = QPushButton("翻译")
        self.translate_button.clicked.connect(self.request_translation)
        self.copy_button = QPushButton("复制文字")
        self.copy_button.setObjectName("primaryButton")
        self.copy_button.clicked.connect(self.copy_text)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        actions.addWidget(self.recapture)
        actions.addWidget(self.translate_button)
        actions.addStretch()
        actions.addWidget(close_button)
        actions.addWidget(self.copy_button)
        layout.addWidget(heading)
        layout.addWidget(self.meta)
        layout.addWidget(self.editor, 1)
        layout.addWidget(self.translation_panel, 1)
        layout.addLayout(actions)

    def show_result(self, result: DisplayResult, auto_copied: bool = False) -> None:
        self.reset_translation()
        self.editor.setPlainText(result.original_text)
        if result.error:
            self.meta.setText(result.error)
            self.meta.setProperty("error", True)
        elif result.original_text:
            prefix = "已自动复制 · " if auto_copied else ""
            self.meta.setText(
                f"{prefix}本机识别用时 {result.ocr_elapsed_ms} ms · 可直接修改"
            )
            self.meta.setProperty("error", False)
        else:
            self.meta.setText("选区中没有检测到文字，请重新框选")
            self.meta.setProperty("error", True)
        self.meta.style().unpolish(self.meta)
        self.meta.style().polish(self.meta)
        self.copy_button.setEnabled(bool(result.original_text))
        self.translate_button.setEnabled(bool(result.original_text))
        self.show()
        self.raise_()
        self.activateWindow()
        if result.original_text:
            self.editor.selectAll()
            self.editor.setFocus()

    def reset_translation(self) -> None:
        self.translation_panel.hide()
        self.translation_editor.clear()
        self.translation_editor.setEnabled(True)
        self.translation_meta.clear()
        self.translation_meta.setProperty("error", False)
        self.copy_translation_button.setEnabled(False)
        self.translate_button.setText("翻译")

    def request_translation(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            return
        self.translation_panel.show()
        self.translation_editor.clear()
        self.translation_editor.setEnabled(False)
        self.translation_editor.setPlaceholderText("正在翻译…")
        self.translation_meta.setText("正在连接 DeepSeek，只会发送上方文字…")
        self.translation_meta.setProperty("error", False)
        self._refresh_translation_meta_style()
        self.copy_translation_button.setEnabled(False)
        self.translate_button.setText("翻译中…")
        self.translate_button.setEnabled(False)
        self.translation_requested.emit(text)

    def show_translation(self, result: TranslationResult) -> None:
        self.translation_panel.show()
        self.translation_editor.setEnabled(True)
        self.translation_editor.setPlaceholderText("译文会显示在这里")
        self.translate_button.setEnabled(bool(self.editor.toPlainText().strip()))
        if result.error:
            self.translation_editor.clear()
            self.translation_meta.setText(result.error)
            self.translation_meta.setProperty("error", True)
            self.copy_translation_button.setEnabled(False)
            self.translate_button.setText("重试翻译")
        else:
            self.translation_editor.setPlainText(result.text or "")
            self.translation_meta.setText(
                f"DeepSeek 翻译用时 {result.elapsed_ms} ms · 可直接修改"
            )
            self.translation_meta.setProperty("error", False)
            self.copy_translation_button.setEnabled(bool(result.text))
            self.translate_button.setText("重新翻译")
        self._refresh_translation_meta_style()

    def _refresh_translation_meta_style(self) -> None:
        self.translation_meta.style().unpolish(self.translation_meta)
        self.translation_meta.style().polish(self.translation_meta)

    def copy_text(self) -> None:
        from PySide6.QtWidgets import QApplication

        text = self.editor.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.meta.setText("已复制到剪贴板")

    def copy_translation(self) -> None:
        from PySide6.QtWidgets import QApplication

        text = self.translation_editor.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.translation_meta.setText("译文已复制到剪贴板")
            self.translation_meta.setProperty("error", False)
            self._refresh_translation_meta_style()


class CaptureOverlay(QWidget):
    selected = Signal(object)
    cancelled = Signal()

    def __init__(self, screen, screenshot: QPixmap) -> None:
        super().__init__(None)
        self._screen = screen
        self._screenshot = screenshot
        self._origin: QPoint | None = None
        self._cursor: QPoint | None = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setGeometry(screen.geometry())
        self.setMouseTracking(True)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def selection_rect(self) -> QRect:
        if self._origin is None or self._cursor is None:
            return QRect()
        return QRect(self._origin, self._cursor).normalized().intersected(self.rect())

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self._screenshot)
        painter.fillRect(self.rect(), QColor(8, 15, 28, 158))
        selected = self.selection_rect()
        if not selected.isEmpty():
            painter.save()
            painter.setClipRect(selected)
            painter.drawPixmap(self.rect(), self._screenshot)
            painter.restore()
            painter.setPen(QPen(QColor("#60A5FA"), 2))
            painter.drawRect(selected.adjusted(0, 0, -1, -1))
            label = f"{selected.width()} × {selected.height()}"
            label_rect = QRect(selected.left(), max(8, selected.top() - 34), 116, 26)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 235))
            painter.drawRoundedRect(label_rect, 6, 6)
            painter.setPen(QColor("white"))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
        else:
            hint = QRect(0, 0, 360, 44)
            hint.moveCenter(QPoint(self.width() // 2, 48))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 230))
            painter.drawRoundedRect(hint, 10, 10)
            painter.setPen(QColor("white"))
            painter.drawText(hint, Qt.AlignmentFlag.AlignCenter, "按住鼠标左键框选文字 · Esc 取消")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._cursor = self._origin
            self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._origin is not None:
            self._cursor = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        self._cursor = event.position().toPoint()
        logical = self.selection_rect()
        if logical.width() < 4 or logical.height() < 4:
            self._origin = None
            self._cursor = None
            self.update()
            return
        image = self._screenshot.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        scale_x = image.width() / max(1, self.width())
        scale_y = image.height() / max(1, self.height())
        pixel = QRect(
            round(logical.x() * scale_x),
            round(logical.y() * scale_y),
            round(logical.width() * scale_x),
            round(logical.height() * scale_y),
        ).intersected(image.rect())
        cropped = image.copy(pixel)
        region = CaptureRegion(
            screen_name=self._screen.name(),
            logical_rect=Rect(logical.x(), logical.y(), logical.width(), logical.height()),
            pixel_rect=Rect(pixel.x(), pixel.y(), pixel.width(), pixel.height()),
            device_pixel_ratio=float(self._screen.devicePixelRatio()),
            image=cropped,
        )
        self.hide()
        self.selected.emit(region)
        self.deleteLater()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
            self.deleteLater()
            return
        super().keyPressEvent(event)


class TrayController(QObject):
    show_requested = Signal()
    capture_requested = Signal()
    live_requested = Signal()
    stop_live_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tray = QSystemTrayIcon(make_app_icon(), parent)
        menu = QMenu()
        show_action = menu.addAction("打开屏幕文字识别")
        capture_action = menu.addAction("开始框选")
        live_action = menu.addAction("持续翻译")
        stop_live_action = menu.addAction("停止持续翻译")
        menu.addSeparator()
        settings_action = menu.addAction("设置")
        quit_action = menu.addAction("退出")
        show_action.triggered.connect(self.show_requested)
        capture_action.triggered.connect(self.capture_requested)
        live_action.triggered.connect(self.live_requested)
        stop_live_action.triggered.connect(self.stop_live_requested)
        settings_action.triggered.connect(self.settings_requested)
        quit_action.triggered.connect(self.quit_requested)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("屏幕文字识别")
        self.tray.activated.connect(self._activated)

    def _activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_requested.emit()

    def show(self) -> None:
        self.tray.show()

    def notify(self, title: str, message: str) -> None:
        if QSystemTrayIcon.supportsMessages():
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2200)
