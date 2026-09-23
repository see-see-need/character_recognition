from __future__ import annotations

import ctypes
import sys
import math

from PySide6.QtCore import QObject, QPointF, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QTextLayout, QTextOption
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel


class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.WindowTransparentForInput
                            | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background: transparent;")


class RegionFrame(TransparentWindow):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#60A5FA"), 2))
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))


class TranslationOverlay(TransparentWindow):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Microsoft YaHei UI", 14))
        self.setStyleSheet('background: transparent; font-family: "Microsoft YaHei UI"; font-size: 18px;')
        self.lines = []
        self.page = 0
        self.page_size = 1
        self.line_height = 28

    def set_text(self, text):
        self.lines = []
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        for paragraph in text.split("\n"):
            layout = QTextLayout(paragraph or " ", self.font())
            layout.setTextOption(option)
            layout.beginLayout()
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(max(1, self.width() - 16))
                encoded = paragraph.encode("utf-16-le")
                start = line.textStart() * 2
                self.lines.append(encoded[start:start + line.textLength() * 2].decode("utf-16-le"))
            layout.endLayout()
        self.page_size = max(1, (self.height() - 16) // self.line_height)
        self.page = 0
        self.update()

    @property
    def page_count(self):
        return max(1, math.ceil(len(self.lines) / self.page_size))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        start = self.page * self.page_size
        for index, text in enumerate(self.lines[start:start + self.page_size]):
            path = QPainterPath()
            path.addText(QPointF(8, 24 + index * self.line_height), self.font(), text)
            painter.strokePath(path, QPen(QColor("#111827"), 3, Qt.PenStyle.SolidLine,
                                         Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.fillPath(path, QColor("white"))


def exclude_from_capture(window):
    if sys.platform != "win32":
        return False
    # WDA_EXCLUDEFROMCAPTURE is supported beginning with Windows 10 2004.
    if sys.getwindowsversion().build < 19041:
        return False
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    function = user32.SetWindowDisplayAffinity
    function.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    function.restype = ctypes.c_bool
    return bool(function(int(window.winId()), 0x11))


class LiveWindows(QObject):
    recapture_requested = Signal()
    stop_requested = Signal()

    def __init__(self):
        super().__init__()
        self.frame = RegionFrame()
        self.translation = TranslationOverlay()
        self.toolbar = QWidget()
        self.toolbar.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                                    | Qt.WindowType.WindowStaysOnTopHint)
        self.toolbar.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        layout = QHBoxLayout(self.toolbar)
        layout.setContentsMargins(6, 4, 6, 4)
        self.previous = QPushButton("上一页")
        self.next = QPushButton("下一页")
        self.page_label = QLabel("1 / 1")
        recapture = QPushButton("重新框选")
        stop = QPushButton("停止")
        for widget in (self.previous, self.page_label, self.next, recapture, stop):
            layout.addWidget(widget)
        self.previous.clicked.connect(lambda: self.turn_page(-1))
        self.next.clicked.connect(lambda: self.turn_page(1))
        recapture.clicked.connect(self.recapture_requested)
        stop.clicked.connect(self.stop_requested)
        self.windows = (self.frame, self.translation, self.toolbar)
        self.capture_excluded = False

    def configure(self, screen, region):
        local = region.logical_rect
        origin = screen.geometry().topLeft()
        rect = QRect(origin.x() + local.x, origin.y() + local.y, local.width, local.height)
        self.frame.setGeometry(rect.adjusted(-2, -2, 2, 2))
        available = screen.availableGeometry()
        self.region_rect = rect
        self.available = available
        width = min(max(rect.width(), 320), available.width())
        self.max_height = min(184, max(72, available.height() // 3))
        self.translation.resize(width, self.max_height)
        self._place(self.max_height)
        self.show()
        self.capture_excluded = all([exclude_from_capture(window) for window in self.windows])

    def _place(self, height):
        rect, available = self.region_rect, self.available
        width = self.translation.width()
        x = min(max(rect.x(), available.left()), available.right() - width + 1)
        y = rect.top() - height - 8
        below = y < available.top()
        if below:
            y = rect.bottom() + 9
        y = min(max(y, available.top()), available.bottom() - height + 1)
        self.translation.setGeometry(x, y, width, height)
        self.toolbar.adjustSize()
        tx = min(x, available.right() - self.toolbar.width() + 1)
        ty = y + height + 4 if below else y - self.toolbar.height() - 4
        if ty < available.top():
            ty = y + height + 4
        ty = min(max(ty, available.top()), available.bottom() - self.toolbar.height() + 1)
        self.toolbar.move(max(available.left(), tx), ty)

    def set_text(self, text):
        self.translation.resize(self.translation.width(), self.max_height)
        self.translation.set_text(text)
        height = min(self.max_height, max(44, len(self.translation.lines) * self.translation.line_height + 16))
        self._place(height)
        self.turn_page(0)

    def turn_page(self, delta):
        view = self.translation
        view.page = min(max(0, view.page + delta), view.page_count - 1)
        self.page_label.setText(f"{view.page + 1} / {view.page_count}")
        self.previous.setEnabled(view.page > 0)
        self.next.setEnabled(view.page + 1 < view.page_count)
        view.update()

    def show(self):
        for window in self.windows:
            window.show()

    def hide(self):
        for window in self.windows:
            window.hide()
