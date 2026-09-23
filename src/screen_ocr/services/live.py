from __future__ import annotations

from dataclasses import replace
from time import monotonic

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QImage

from screen_ocr.core.models import ProcessingStatus


def fingerprint(image):
    gray = image.convertToFormat(QImage.Format.Format_Grayscale8)
    data = np.frombuffer(gray.constBits(), np.uint8, count=gray.sizeInBytes())
    return data.reshape(gray.height(), gray.bytesPerLine())[:, :gray.width()].copy()


def changed(left, right):
    if left is None or left.shape != right.shape:
        return True
    delta = np.abs(left.astype(np.int16) - right.astype(np.int16))
    return bool(np.mean(delta > 18) > 0.001)


class LiveController(QObject):
    stopped = Signal(str)

    def __init__(self, app, ocr, translation, windows):
        super().__init__()
        self.app, self.ocr, self.translation, self.windows = app, ocr, translation, windows
        self.active = False
        self.paused = False
        self.session = 0
        self.version = 0
        self.inflight = None
        self.pending = None
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.sample)
        self.retry = QTimer(self)
        self.retry.setSingleShot(True)
        self.retry.setInterval(30000)
        self.retry.timeout.connect(self.translate)
        self.translation.completed.connect(self.translation_completed)
        self.last_text = None
        self.blocked = False
        self.sampling = False

    def start(self, region):
        self.stop()
        self.screen = next((s for s in self.app.screens() if s.name() == region.screen_name), None)
        if self.screen is None:
            self.stopped.emit("显示器不可用，请重新框选")
            return
        self.region = region
        self.geometry = self.screen.geometry()
        self.scale = self.screen.devicePixelRatio()
        self.active, self.paused = True, False
        self.last_frame = fingerprint(region.image)
        self.submitted_frame = self.last_frame
        self.dirty_since = None
        self.last_text = None
        self.blocked = False
        self.windows.configure(self.screen, region)
        self.windows.set_text("正在识别…")
        self.pending = (self.session, self.version, region)
        self.dispatch()
        self.timer.start()

    def stop(self, message=""):
        was_active = self.active
        self.active = False
        self.paused = False
        self.session += 1
        self.timer.stop()
        self.retry.stop()
        self.pending = None
        self.translation.invalidate()
        self.windows.hide()
        if was_active:
            self.stopped.emit(message or "已停止持续翻译")

    def pause(self):
        if not self.active:
            return
        self.paused = True
        self.session += 1
        self.pending = None
        self.timer.stop()
        self.retry.stop()
        self.translation.invalidate()
        self.windows.hide()

    def resume(self):
        if not self.active:
            return
        self.paused = False
        self.last_frame = None
        self.submitted_frame = None
        self.last_text = None
        self.dirty_since = None
        self.windows.show()
        self.timer.start()
        self.sample()

    def sample(self):
        if not self.active or self.paused or self.sampling:
            return
        if (self.screen not in self.app.screens() or self.screen.geometry() != self.geometry
                or self.screen.devicePixelRatio() != self.scale):
            self.stop("显示器布局或缩放已改变，请重新框选")
            return
        if not self.windows.capture_excluded:
            self.sampling = True
            self.windows.hide()
            token = self.session
            QTimer.singleShot(60, lambda: self.capture_sample(token))
        else:
            self.capture_sample(self.session)

    def capture_sample(self, token):
        self.sampling = False
        if not self.active or self.paused or token != self.session:
            return
        if (self.screen not in self.app.screens() or self.screen.geometry() != self.geometry
                or self.screen.devicePixelRatio() != self.scale):
            self.stop("显示器布局或缩放已改变，请重新框选")
            return
        image = self.screen.grabWindow(0).toImage()
        if not self.windows.capture_excluded:
            self.windows.show()
        if image.isNull():
            self.windows.set_text("无法读取屏幕，正在重试…")
            return
        rect = self.region.logical_rect
        sx = image.width() / self.geometry.width()
        sy = image.height() / self.geometry.height()
        crop = image.copy(round(rect.x * sx), round(rect.y * sy),
                          round(rect.right * sx) - round(rect.x * sx),
                          round(rect.bottom * sy) - round(rect.y * sy))
        self.accept_frame(replace(self.region, image=crop), monotonic())

    def accept_frame(self, region, now):
        current = fingerprint(region.image)
        unstable = changed(self.last_frame, current)
        self.last_frame = current
        if not changed(self.submitted_frame, current):
            self.dirty_since = None
            return
        if self.dirty_since is None:
            self.dirty_since = now
        if unstable and now - self.dirty_since < 2:
            return
        self.version += 1
        self.submitted_frame = current
        self.dirty_since = None
        self.pending = (self.session, self.version, region)
        self.dispatch()

    def dispatch(self):
        if self.active and not self.paused and self.pending and not self.ocr.busy:
            job = self.pending
            if self.ocr.submit(job[2]):
                self.inflight = job[:2]
                self.pending = None

    def ocr_completed(self, result):
        if self.inflight is None:
            return False
        token = self.inflight
        self.inflight = None
        if self.active and not self.paused and token == (self.session, self.version):
            if result.status == ProcessingStatus.ERROR:
                self.windows.set_text(result.error or "识别失败，正在重试…")
                self.submitted_frame = None
            else:
                text = result.text.strip()
                if text != self.last_text:
                    self.last_text = text
                    self.retry.stop()
                    self.translation.invalidate()
                    if not text:
                        self.windows.set_text("")
                    elif not self.blocked:
                        self.translate()
        self.dispatch()
        return True

    def translate(self):
        if self.active and not self.paused and not self.blocked and self.last_text:
            self.windows.set_text("正在翻译…")
            self.translation.submit(self.last_text)

    def translation_completed(self, result):
        if not self.active or self.paused:
            return
        if result.error:
            self.blocked = any(word in result.error for word in ("API Key", "余额", "凭据"))
            self.windows.set_text(result.error + ("" if self.blocked else "；30 秒后自动重试"))
            if not self.blocked:
                self.retry.start()
        else:
            self.retry.stop()
            self.windows.set_text(result.text or "")

    def settings_updated(self):
        self.blocked = False
        self.retry.stop()
        self.translate()
