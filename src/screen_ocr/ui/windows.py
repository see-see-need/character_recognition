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

from screen_ocr.core.models import AppSettings, CaptureRegion, DisplayResult, Rect


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
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._allow_close = False
        self.setWindowTitle("屏幕文字识别")
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(460, 330)
        self.resize(520, 360)

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
        layout.addWidget(shortcut_frame)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.setCentralWidget(body)

    def set_processing(self, processing: bool, message: str) -> None:
        self.capture_button.setDisabled(processing)
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
    def __init__(self, settings: AppSettings, parent=None) -> None:
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
        note = QLabel("翻译接口已预留，首版不会上传或翻译任何内容。")
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
        layout.addWidget(note)
        layout.addSpacing(8)
        layout.addWidget(buttons)

    def values(self, previous: AppSettings) -> AppSettings:
        return AppSettings(
            hotkey=self.hotkey_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            auto_copy=self.auto_copy.isChecked(),
            start_at_login=self.startup.isChecked(),
            translation=previous.translation,
        )


class ResultDialog(QDialog):
    recapture_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("识别结果")
        self.setWindowIcon(make_app_icon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.resize(620, 430)
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
        actions = QHBoxLayout()
        self.recapture = QPushButton("重新框选")
        self.recapture.clicked.connect(self.recapture_requested)
        self.copy_button = QPushButton("复制文字")
        self.copy_button.setObjectName("primaryButton")
        self.copy_button.clicked.connect(self.copy_text)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        actions.addWidget(self.recapture)
        actions.addStretch()
        actions.addWidget(close_button)
        actions.addWidget(self.copy_button)
        layout.addWidget(heading)
        layout.addWidget(self.meta)
        layout.addWidget(self.editor, 1)
        layout.addLayout(actions)

    def show_result(self, result: DisplayResult, auto_copied: bool = False) -> None:
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
        self.show()
        self.raise_()
        self.activateWindow()
        if result.original_text:
            self.editor.selectAll()
            self.editor.setFocus()

    def copy_text(self) -> None:
        from PySide6.QtWidgets import QApplication

        text = self.editor.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.meta.setText("已复制到剪贴板")


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
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.tray = QSystemTrayIcon(make_app_icon(), parent)
        menu = QMenu()
        show_action = menu.addAction("打开屏幕文字识别")
        capture_action = menu.addAction("开始框选")
        menu.addSeparator()
        settings_action = menu.addAction("设置")
        quit_action = menu.addAction("退出")
        show_action.triggered.connect(self.show_requested)
        capture_action.triggered.connect(self.capture_requested)
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
