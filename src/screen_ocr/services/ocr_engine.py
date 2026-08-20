from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from screen_ocr.core.models import OcrLine, OcrResult, ProcessingStatus, Rect
from screen_ocr.core.text import choose_recognition, join_lines, sort_reading_order


DETECTION_MODEL = "PP-OCRv5_mobile_det"
PRIMARY_MODEL = "PP-OCRv5_mobile_rec"
KOREAN_MODEL = "korean_PP-OCRv5_mobile_rec"


def application_root() -> Path:
    if getattr(__import__("sys"), "frozen", False):
        return Path(getattr(__import__("sys"), "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parents[3]


def model_directory(model_name: str) -> Path | None:
    candidate = application_root() / "models" / model_name
    return candidate if candidate.exists() else None


def _result_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        payload = result
    else:
        payload = getattr(result, "json", None)
        if callable(payload):
            payload = payload()
        if payload is None:
            try:
                payload = dict(result)
            except (TypeError, ValueError):
                payload = {}
        if isinstance(payload, str):
            payload = json.loads(payload)
    if isinstance(payload, dict) and isinstance(payload.get("res"), dict):
        return payload["res"]
    return payload if isinstance(payload, dict) else {}


def _first_prediction(model: Any, image: np.ndarray) -> dict[str, Any]:
    output = model.predict(input=image, batch_size=1)
    first = next(iter(output), None)
    return _result_dict(first) if first is not None else {}


def _crop_box(image: np.ndarray, points: np.ndarray) -> tuple[np.ndarray, Rect]:
    xs = points[:, 0]
    ys = points[:, 1]
    height, width = image.shape[:2]
    left = max(0, int(np.floor(xs.min())) - 2)
    top = max(0, int(np.floor(ys.min())) - 2)
    right = min(width, int(np.ceil(xs.max())) + 3)
    bottom = min(height, int(np.ceil(ys.max())) + 3)
    return image[top:bottom, left:right].copy(), Rect(left, top, right - left, bottom - top)


class PaddleOcrEngine:
    """Lazy, offline-first OCR engine with one detector and two recognizers."""

    def __init__(self) -> None:
        self._detector: Any | None = None
        self._primary: Any | None = None
        self._korean: Any | None = None

    def _load(self) -> None:
        if self._detector is not None:
            return
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        from paddleocr import TextDetection, TextRecognition

        detector_dir = model_directory(DETECTION_MODEL)
        primary_dir = model_directory(PRIMARY_MODEL)
        korean_dir = model_directory(KOREAN_MODEL)
        if getattr(sys, "frozen", False) and not all(
            (detector_dir, primary_dir, korean_dir)
        ):
            raise RuntimeError("便携程序缺少离线 OCR 模型，请重新生成完整发布目录")
        # Paddle 3.3.1's Windows oneDNN path cannot execute PP-OCRv5 array
        # attributes reliably. The plain CPU executor is stable and remains
        # fully local; keep this explicit so packaged builds behave the same.
        common = {
            "device": "cpu",
            "engine": "paddle_static",
            "enable_mkldnn": False,
            "cpu_threads": 4,
        }
        self._detector = TextDetection(
            model_name=DETECTION_MODEL,
            model_dir=str(detector_dir) if detector_dir else None,
            **common,
        )
        self._primary = TextRecognition(
            model_name=PRIMARY_MODEL,
            model_dir=str(primary_dir) if primary_dir else None,
            **common,
        )
        self._korean = TextRecognition(
            model_name=KOREAN_MODEL,
            model_dir=str(korean_dir) if korean_dir else None,
            **common,
        )

    @staticmethod
    def _recognize(model: Any, crop: np.ndarray) -> tuple[str, float]:
        data = _first_prediction(model, crop)
        text = str(data.get("rec_text", "")).strip()
        try:
            score = float(data.get("rec_score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        return text, score

    def recognize(self, image: np.ndarray) -> OcrResult:
        started = time.perf_counter()
        try:
            self._load()
            if image.size == 0 or min(image.shape[:2]) < 4:
                return OcrResult(
                    text="",
                    status=ProcessingStatus.EMPTY,
                    error="选区太小，请重新框选",
                )
            if image.ndim == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            detection = _first_prediction(self._detector, image)
            polygons = np.asarray(detection.get("dt_polys", []), dtype=np.float32)
            lines: list[OcrLine] = []
            for polygon in polygons:
                if polygon.shape != (4, 2):
                    continue
                crop, bounds = _crop_box(image, polygon)
                if crop.size == 0:
                    continue
                primary = self._recognize(self._primary, crop)
                korean = self._recognize(self._korean, crop)
                text, confidence, model = choose_recognition(primary, korean)
                if text and confidence >= 0.25:
                    lines.append(OcrLine(text, bounds, confidence, model))
            lines = sort_reading_order(lines)
            text = join_lines(lines)
            elapsed = round((time.perf_counter() - started) * 1000)
            if not text:
                return OcrResult(
                    text="",
                    elapsed_ms=elapsed,
                    status=ProcessingStatus.EMPTY,
                    error="选区中没有检测到可识别文字",
                )
            hint = "ko" if any(line.model == KOREAN_MODEL for line in lines) else "auto"
            return OcrResult(text, tuple(lines), hint, elapsed)
        except Exception as exc:  # boundary: third-party inference errors
            elapsed = round((time.perf_counter() - started) * 1000)
            return OcrResult(
                text="",
                elapsed_ms=elapsed,
                status=ProcessingStatus.ERROR,
                error=f"OCR 初始化或识别失败：{exc}",
            )
