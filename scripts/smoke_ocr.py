from __future__ import annotations

from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from screen_ocr.services.ocr_engine import PaddleOcrEngine


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    canvas = Image.new("RGB", (940, 390), "white")
    draw = ImageDraw.Draw(canvas)
    fonts = {
        "cjk": ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 42),
        "jp": ImageFont.truetype(r"C:\Windows\Fonts\YuGothM.ttc", 42),
        "ko": ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 42),
    }
    rows = [
        ("简体中文：屏幕识别", fonts["cjk"]),
        ("繁體中文：螢幕辨識", fonts["cjk"]),
        ("English: Screen OCR", fonts["cjk"]),
        ("日本語：画面の文字", fonts["jp"]),
        ("한국어: 화면 문자", fonts["ko"]),
    ]
    for index, (text, font) in enumerate(rows):
        draw.text((32, 22 + index * 70), text, font=font, fill="#111827")
    image = cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR)
    result = PaddleOcrEngine().recognize(image)
    print(result.text)
    print(f"status={result.status} lines={len(result.lines)} elapsed_ms={result.elapsed_ms}")
    for line in result.lines:
        print(f"{line.model}: {line.confidence:.3f} {line.text}")
    if not result.text or len(result.lines) < 4:
        raise SystemExit(result.error or "OCR smoke test did not detect enough lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
