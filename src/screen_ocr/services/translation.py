from __future__ import annotations

import asyncio
from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot

from screen_ocr.core.models import TranslationJob, TranslationRequest, TranslationResult
from screen_ocr.core.translation import TranslationProvider
from screen_ocr.services.credentials import CredentialStore
from screen_ocr.services.deepseek import DeepSeekTranslationProvider


ProviderFactory = Callable[[str], TranslationProvider]


class TranslationWorker(QObject):
    completed = Signal(object, object)

    def __init__(
        self,
        credential_store: CredentialStore,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        super().__init__()
        self._credentials = credential_store
        self._provider_factory = provider_factory or DeepSeekTranslationProvider

    @Slot(object)
    def translate(self, job: TranslationJob) -> None:
        try:
            api_key = self._credentials.get("deepseek")
        except OSError:
            result = TranslationResult(
                text=None,
                provider="deepseek",
                error="无法读取已保存的 DeepSeek API Key，请在设置中重新保存",
            )
        else:
            if not api_key:
                result = TranslationResult(
                    text=None,
                    provider="deepseek",
                    error="尚未配置 DeepSeek API Key，请前往设置填写",
                )
            else:
                try:
                    provider = self._provider_factory(api_key)
                    request = TranslationRequest(
                        text=job.text,
                        source_language=job.source_language,
                        target_language=job.target_language,
                    )
                    result = asyncio.run(provider.translate(request, asyncio.Event()))
                except Exception:
                    result = TranslationResult(
                        text=None,
                        provider="deepseek",
                        error="翻译服务发生意外错误，请重试",
                    )
        self.completed.emit(job, result)


class TranslationService(QObject):
    _request = Signal(object)
    completed = Signal(object)

    def __init__(
        self,
        credential_store: CredentialStore,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        super().__init__()
        self._latest_job_id = 0
        self._thread = QThread(self)
        self._worker = TranslationWorker(credential_store, provider_factory)
        self._worker.moveToThread(self._thread)
        self._request.connect(self._worker.translate)
        self._worker.completed.connect(self._on_completed)
        self._thread.start()

    def submit(self, text: str) -> int:
        self._latest_job_id += 1
        job = TranslationJob(job_id=self._latest_job_id, text=text)
        self._request.emit(job)
        return job.job_id

    def invalidate(self) -> None:
        self._latest_job_id += 1

    @Slot(object, object)
    def _on_completed(
        self, job: TranslationJob, result: TranslationResult
    ) -> None:
        if job.job_id == self._latest_job_id:
            self.completed.emit(result)

    def shutdown(self) -> None:
        self.invalidate()
        self._thread.quit()
        self._thread.wait()
