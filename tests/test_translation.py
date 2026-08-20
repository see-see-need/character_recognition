import asyncio

import pytest

from screen_ocr.core.models import (
    OcrResult,
    ProcessingStatus,
    TranslationResult,
    TranslationSettings,
)
from screen_ocr.core.translation import TextPipeline


class FakeProvider:
    name = "fake"

    async def translate(self, request, cancel_event):
        assert request.target_language == "zh-Hans"
        return TranslationResult("你好", "en", self.name, 12)


class FailingProvider:
    name = "fail"

    async def translate(self, request, cancel_event):
        return TranslationResult(None, provider=self.name, error="service unavailable")


@pytest.mark.asyncio
async def test_disabled_translation_passes_through() -> None:
    result = await TextPipeline().process(OcrResult("Hello"), TranslationSettings())
    assert result.original_text == "Hello"
    assert result.translated_text is None


@pytest.mark.asyncio
async def test_provider_can_be_inserted() -> None:
    pipeline = TextPipeline({"fake": FakeProvider()})
    result = await pipeline.process(
        OcrResult("Hello"), TranslationSettings(True, "fake", "zh-Hans")
    )
    assert result.original_text == "Hello"
    assert result.translated_text == "你好"


@pytest.mark.asyncio
async def test_translation_failure_keeps_original() -> None:
    pipeline = TextPipeline({"fail": FailingProvider()})
    result = await pipeline.process(
        OcrResult("Hello"), TranslationSettings(True, "fail", "zh-Hans")
    )
    assert result.status == ProcessingStatus.SUCCESS
    assert result.original_text == "Hello"
    assert result.translated_text is None
    assert result.error == "service unavailable"

