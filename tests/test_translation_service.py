import asyncio

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
