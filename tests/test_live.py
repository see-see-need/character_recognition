from types import SimpleNamespace
import pytest

from PySide6.QtCore import QObject, QRect, Signal, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from screen_ocr.core.models import CaptureRegion, Rect, OcrResult, TranslationResult
from screen_ocr.services.live import LiveController
from screen_ocr.ui.live import LiveWindows


class FakeTranslation(QObject):
    completed = Signal(object)

    def __init__(self):
        super().__init__()
        self.requests = []
        self.invalidations = 0

    def submit(self, text):
        self.requests.append(text)

    def invalidate(self):
        self.invalidations += 1


class FakeOcr:
    busy = False

    def __init__(self):
        self.requests = []

    def submit(self, region):
        if self.busy:
            return False
        self.busy = True
        self.requests.append(region)
        return True


class FakeWindows:
    capture_excluded = True

    def configure(self, screen, region):
        pass

    def set_text(self, text):
        self.text = text

    def show(self):
        pass

    def hide(self):
        pass


def region(shade=0):
    image = QImage(80, 40, QImage.Format.Format_RGB32)
    image.fill(shade)
    return CaptureRegion("test", Rect(0, 0, 80, 40), Rect(0, 0, 80, 40), 1, image)


def controller():
    screen = SimpleNamespace(name=lambda: "test", geometry=lambda: QRect(0, 0, 1000, 800),
                             devicePixelRatio=lambda: 1)
    app = SimpleNamespace(screens=lambda: [screen])
    value = LiveController(app, FakeOcr(), FakeTranslation(), FakeWindows())
    value.start(region())
    value.timer.stop()
    return value


def complete(value, text):
    value.ocr.busy = False
    assert value.ocr_completed(OcrResult(text))


def test_first_frame_translates_and_unchanged_frames_do_not_repeat():
    value = controller()
    complete(value, "Hello")
    assert value.translation.requests == ["Hello"]
    for now in range(10):
        value.accept_frame(region(), now)
    assert len(value.ocr.requests) == 1
    value.stop()


def test_change_debounces_and_same_text_does_not_retranslate():
    value = controller()
    complete(value, "Hello")
    value.accept_frame(region(0xFFFFFF), 1)
    assert len(value.ocr.requests) == 1
    value.accept_frame(region(0xFFFFFF), 1.5)
    complete(value, "Hello")
    assert value.translation.requests == ["Hello"]
    value.accept_frame(region(), 2)
    value.accept_frame(region(), 2.5)
    complete(value, "World")
    assert value.translation.requests == ["Hello", "World"]
    assert value.windows.text == "正在翻译…"
    value.stop()


def test_latest_pending_frame_replaces_old_frame_and_old_result_is_ignored():
    value = controller()
    for shade, now in [(0xFFFFFF, 1), (0xFFFFFF, 1.5), (0x888888, 2), (0x888888, 2.5)]:
        value.accept_frame(region(shade), now)
    complete(value, "obsolete")
    assert not value.translation.requests
    assert len(value.ocr.requests) == 2
    complete(value, "latest")
    assert value.translation.requests == ["latest"]
    value.stop()


def test_continuous_animation_forces_sample_after_two_seconds():
    value = controller()
    complete(value, "first")
    for index in range(5):
        value.accept_frame(region(0x222222 * (index + 1)), 1 + index * .5)
    assert len(value.ocr.requests) == 2
    value.stop()


def test_empty_clears_and_stop_discards_late_result():
    value = controller()
    complete(value, "")
    assert value.windows.text == ""
    assert not value.translation.requests
    value.accept_frame(region(0xFFFFFF), 1)
    value.accept_frame(region(0xFFFFFF), 1.5)
    value.stop()
    complete(value, "late")
    assert not value.translation.requests
    assert not value.timer.isActive()


def test_network_recovery_and_credentials_pause():
    value = controller()
    complete(value, "Hello")
    value.translation_completed(TranslationResult(None, error="连接超时"))
    assert value.retry.isActive()
    value.retry.stop()
    value.translate()
    assert value.translation.requests == ["Hello", "Hello"]
    value.translation_completed(TranslationResult(None, error="API Key 无效"))
    assert value.blocked
    value.translate()
    assert len(value.translation.requests) == 2
    value.settings_updated()
    assert len(value.translation.requests) == 3
    value.stop()


def test_pause_resume_invalidates_old_ocr():
    value = controller()
    value.pause()
    complete(value, "late")
    assert not value.translation.requests
    # Resume's next sample starts with a fresh baseline even if content is identical.
    value.sample = lambda: None
    value.resume()
    assert value.submitted_frame is None
    assert value.last_text is None
    value.stop()


def test_transparent_windows_pagination_and_screen_bounds():
    screen = QApplication.instance().primaryScreen()
    windows = LiveWindows()
    sample = region()
    sample.screen_name = screen.name()
    windows.configure(screen, sample)
    windows.set_text("很长的译文，需要分页。" * 300)
    assert windows.translation.page_count > 1
    lines = "".join(windows.translation.lines)
    assert lines == "很长的译文，需要分页。" * 300
    windows.turn_page(1)
    assert windows.translation.page == 1
    for window in (windows.frame, windows.translation):
        assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        assert window.windowFlags() & Qt.WindowType.WindowTransparentForInput
        assert window.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert screen.availableGeometry().contains(windows.translation.geometry())
    windows.hide()


def test_display_change_stops_and_invalidates_session():
    value = controller()
    old_session = value.session
    value.app.screens = lambda: []
    messages = []
    value.stopped.connect(messages.append)
    value.sample()
    assert not value.active
    assert value.session > old_session
    assert "重新框选" in messages[-1]


@pytest.mark.parametrize("scale", [1, 1.5, 2])
def test_sampling_maps_logical_region_to_physical_pixels(scale):
    value = controller()
    value.region.logical_rect = Rect(10, 20, 80, 40)
    value.scale = scale
    value.screen.devicePixelRatio = lambda: scale
    image = QImage(round(1000 * scale), round(800 * scale), QImage.Format.Format_RGB32)
    image.fill(0xFFFFFF)
    value.screen.grabWindow = lambda _: SimpleNamespace(toImage=lambda: image)
    captured = []
    value.accept_frame = lambda crop, now: captured.append(crop)
    value.capture_sample(value.session)
    assert captured[0].image.width() == round(80 * scale)
    assert captured[0].image.height() == round(40 * scale)
    value.stop()


def test_overlay_supports_negative_secondary_screen_coordinates():
    screen = SimpleNamespace(geometry=lambda: QRect(-1920, 0, 1920, 1080),
                             availableGeometry=lambda: QRect(-1920, 0, 1920, 1040))
    windows = LiveWindows()
    windows.configure(screen, region())
    windows.set_text("译文")
    assert windows.frame.x() == -1922
    assert screen.availableGeometry().contains(windows.translation.geometry())
    assert screen.availableGeometry().contains(windows.toolbar.geometry())
    windows.hide()


def test_controller_routes_live_result_without_dialog_or_clipboard(monkeypatch):
    import screen_ocr.app as module
    from screen_ocr.core.models import AppSettings

    class Ocr(QObject):
        completed = Signal(object)
        busy = False

        def submit(self, capture):
            if self.busy:
                return False
            self.busy = True
            return True

        def shutdown(self):
            pass

    class Translation(FakeTranslation):
        def shutdown(self):
            pass

    monkeypatch.setattr(module, "OcrService", Ocr)
    monkeypatch.setattr(module, "TranslationService", lambda *args: Translation())
    monkeypatch.setattr(module.SettingsStore, "load", lambda self: AppSettings())
    app = QApplication.instance()
    controller = module.ApplicationController(app)
    controller.capture.begin = lambda: None
    app.clipboard().setText("keep clipboard")
    sample = region()
    sample.screen_name = app.primaryScreen().name()
    controller._capture_mode = "live"
    controller._recognize(sample)
    controller.live.timer.stop()
    controller.ocr.busy = False
    controller.ocr.completed.emit(OcrResult("Hello"))
    assert controller.live_translation.requests == ["Hello"]
    assert controller.result.isHidden()
    assert app.clipboard().text() == "keep clipboard"
    controller.live_translation.completed.emit(TranslationResult("你好"))
    assert controller.live_windows.translation.lines == ["你好"]

    # Recapture cancellation restores the same region, without restoring result UI.
    controller.start_live()
    assert controller.live.paused
    controller.live.sample = lambda: None
    controller._capture_cancelled()
    assert controller.live.active and not controller.live.paused
    assert controller.result.isHidden()

    # A normal capture ends the live session; an old live OCR cannot open a dialog.
    controller.live.inflight = (controller.live.session, controller.live.version)
    controller.ocr.busy = True
    controller.start_capture()
    assert not controller.live.active
    controller._recognize(sample)
    assert controller._pending_normal is sample
    controller.ocr.busy = False
    controller.ocr.completed.emit(OcrResult("late live text"))
    assert controller.result.isHidden()
    assert controller.ocr.busy
    controller.ocr.busy = False
    controller.ocr.completed.emit(OcrResult("normal text"))
    assert controller.result.editor.toPlainText() == "normal text"
    assert app.clipboard().text() == "normal text"
    controller.result.close()
    controller.main.hide()
    controller.live.stop()
    controller.deleteLater()
