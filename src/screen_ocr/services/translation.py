from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal, Slot

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
        result = asyncio.run(self.translate_async(job))
        self.completed.emit(job, result)

    async def translate_async(self, job: TranslationJob) -> TranslationResult:
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
                    result = await provider.translate(request, asyncio.Event())
                except Exception:
                    result = TranslationResult(
                        text=None,
                        provider="deepseek",
                        error="翻译服务发生意外错误，请重试",
                    )
        return result


class TranslationService(QObject):
    _finished = Signal(object, object)
    completed = Signal(object)

    def __init__(
        self,
        credential_store: CredentialStore,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        super().__init__()
        self._latest_job_id = 0
        self._loop = asyncio.new_event_loop()
        self._worker = TranslationWorker(credential_store, provider_factory)
        self._finished.connect(self._on_completed)
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._future = None
        self._closed = False
        self._thread.start()

    def submit(self, text: str) -> int:
        self.invalidate()
        job = TranslationJob(job_id=self._latest_job_id, text=text)
        if not self._closed:
            self._future = asyncio.run_coroutine_threadsafe(self._run(job), self._loop)
        return job.job_id

    async def _run(self, job: TranslationJob) -> None:
        result = await self._worker.translate_async(job)
        self._finished.emit(job, result)

    def invalidate(self) -> None:
        self._latest_job_id += 1
        if self._future is not None:
            self._future.cancel()
            self._future = None

    @Slot(object, object)
    def _on_completed(
        self, job: TranslationJob, result: TranslationResult
    ) -> None:
        if job.job_id == self._latest_job_id:
            self.completed.emit(result)

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.invalidate()
        async def drain():
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.run_coroutine_threadsafe(drain(), self._loop).result(timeout=5)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._loop.close()
