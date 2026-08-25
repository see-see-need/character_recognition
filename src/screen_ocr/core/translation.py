from __future__ import annotations

import asyncio
from typing import Protocol

from .models import (
    DisplayResult,
    OcrResult,
    ProcessingStatus,
    TranslationRequest,
    TranslationResult,
    TranslationSettings,
)


class TranslationProvider(Protocol):
    name: str

    async def translate(
        self, request: TranslationRequest, cancel_event: asyncio.Event
    ) -> TranslationResult: ...


class NullTranslationProvider:
    name = "none"

    async def translate(
        self, request: TranslationRequest, cancel_event: asyncio.Event
    ) -> TranslationResult:
        return TranslationResult(text=None, provider=self.name, error="未配置翻译服务")


class TextPipeline:
    """Provider-neutral post-OCR translation pipeline."""

    def __init__(self, providers: dict[str, TranslationProvider] | None = None) -> None:
        self._providers = providers or {}

    async def translate(
        self,
        ocr: OcrResult,
        settings: TranslationSettings,
        cancel_event: asyncio.Event | None = None,
    ) -> DisplayResult:
        if ocr.status != ProcessingStatus.SUCCESS:
            return DisplayResult(
                original_text=ocr.text,
                status=ocr.status,
                error=ocr.error,
                ocr_elapsed_ms=ocr.elapsed_ms,
            )
        provider = self._providers.get(settings.provider)
        if provider is None:
            return DisplayResult(
                original_text=ocr.text,
                status=ProcessingStatus.SUCCESS,
                error="翻译服务不可用，已保留识别原文",
                ocr_elapsed_ms=ocr.elapsed_ms,
            )
        request = TranslationRequest(
            text=ocr.text,
            source_language=ocr.language_hint,
            target_language=settings.target_language,
        )
        result = await provider.translate(request, cancel_event or asyncio.Event())
        return DisplayResult(
            original_text=ocr.text,
            translated_text=result.text,
            status=ProcessingStatus.SUCCESS,
            error=result.error,
            ocr_elapsed_ms=ocr.elapsed_ms,
            translation_elapsed_ms=result.elapsed_ms,
        )

    async def process(
        self,
        ocr: OcrResult,
        settings: TranslationSettings,
        cancel_event: asyncio.Event | None = None,
    ) -> DisplayResult:
        """Backward-compatible alias for callers that explicitly request translation."""
        return await self.translate(ocr, settings, cancel_event)

    @staticmethod
    def without_translation(ocr: OcrResult) -> DisplayResult:
        return DisplayResult(
            original_text=ocr.text,
            status=ocr.status,
            error=ocr.error,
            ocr_elapsed_ms=ocr.elapsed_ms,
        )
