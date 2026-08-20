from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ProcessingStatus(StrEnum):
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass(slots=True)
class CaptureRegion:
    screen_name: str
    logical_rect: Rect
    pixel_rect: Rect
    device_pixel_ratio: float
    image: Any = field(repr=False)


@dataclass(frozen=True, slots=True)
class OcrLine:
    text: str
    bounds: Rect
    confidence: float
    model: str


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    lines: tuple[OcrLine, ...] = ()
    language_hint: str = "auto"
    elapsed_ms: int = 0
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    text: str
    source_language: str = "auto"
    target_language: str = "zh-Hans"


@dataclass(frozen=True, slots=True)
class TranslationResult:
    text: str | None
    detected_source_language: str = "auto"
    provider: str = "none"
    elapsed_ms: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class DisplayResult:
    original_text: str
    translated_text: str | None = None
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    error: str | None = None
    ocr_elapsed_ms: int = 0
    translation_elapsed_ms: int = 0


@dataclass(frozen=True, slots=True)
class TranslationSettings:
    enabled: bool = False
    provider: str = ""
    target_language: str = "zh-Hans"


@dataclass(frozen=True, slots=True)
class AppSettings:
    hotkey: str = "Ctrl+Shift+S"
    auto_copy: bool = True
    start_at_login: bool = False
    translation: TranslationSettings = TranslationSettings()


def logical_to_pixel_rect(rect: Rect, device_pixel_ratio: float) -> Rect:
    """Convert a Qt logical rectangle to a covering physical-pixel rectangle."""
    left = round(rect.x * device_pixel_ratio)
    top = round(rect.y * device_pixel_ratio)
    right = round(rect.right * device_pixel_ratio)
    bottom = round(rect.bottom * device_pixel_ratio)
    return Rect(left, top, max(0, right - left), max(0, bottom - top))

