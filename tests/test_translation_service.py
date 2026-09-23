import asyncio
import threading
import time

from PySide6.QtCore import QCoreApplication

from screen_ocr.core.models import TranslationJob, TranslationResult
from screen_ocr.services.translation import TranslationService, TranslationWorker


class MemoryCredentials:
    def __init__(self, value=None):
        self.value = value

    def get(self, provider):
        return self.value

    def set(self, provider, secret):
        self.value = secret

    def delete(self, provider):
        self.value = None


class FakeProvider:
    name = "deepseek"

    async def translate(self, request, cancel_event: asyncio.Event):
        return TranslationResult(f"译文：{request.text}", provider=self.name)


def test_worker_reports_missing_key() -> None:
    worker = TranslationWorker(MemoryCredentials())
    results = []
    worker.completed.connect(lambda job, result: results.append(result))
    worker.translate(TranslationJob(1, "Hello"))
    assert "尚未配置" in results[0].error


def test_worker_translates_with_injected_provider() -> None:
    worker = TranslationWorker(MemoryCredentials("secret"), lambda key: FakeProvider())
    results = []
    worker.completed.connect(lambda job, result: results.append((job, result)))
    worker.translate(TranslationJob(4, "Hello"))
    assert results[0][0].job_id == 4
    assert results[0][1].text == "译文：Hello"


def test_service_ignores_stale_results() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    service = TranslationService(MemoryCredentials("secret"), lambda key: FakeProvider())
    received = []
    service.completed.connect(received.append)
    service._latest_job_id = 2
    result = TranslationResult("旧译文", provider="deepseek")
    service._on_completed(TranslationJob(1, "old"), result)
    assert received == []
    service._on_completed(TranslationJob(2, "current"), result)
    assert received == [result]
    service.shutdown()
    assert app is not None


def test_new_request_cancels_inflight_network_wait():
    started = threading.Event()
    cancelled = threading.Event()

    class BlockingProvider:
        async def translate(self, request, cancel_event):
            if request.text == "old":
                started.set()
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    cancelled.set()
                    raise
            return TranslationResult("new result")

    service = TranslationService(MemoryCredentials("secret"), lambda key: BlockingProvider())
    received = []
    service.completed.connect(received.append)
    try:
        service.submit("old")
        assert started.wait(2)
        service.submit("new")
        assert cancelled.wait(2)
        deadline = time.monotonic() + 2
        while not received and time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(.005)
        assert [r.text for r in received] == ["new result"]
    finally:
        service.shutdown()


def test_shutdown_cancels_active_request_without_waiting_for_timeout():
    started = threading.Event()
    cancelled = threading.Event()

    class BlockingProvider:
        async def translate(self, request, cancel_event):
            started.set()
            try:
                await asyncio.sleep(60)
            finally:
                cancelled.set()

    service = TranslationService(MemoryCredentials("secret"), lambda key: BlockingProvider())
    service.submit("old")
    assert started.wait(2)
    service.shutdown()
    assert cancelled.is_set()
