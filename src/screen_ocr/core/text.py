from __future__ import annotations

import re
from collections.abc import Iterable

from .models import OcrLine, Rect


_HANGUL_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")


def contains_hangul(text: str) -> bool:
    return bool(_HANGUL_RE.search(text))


def choose_recognition(
    primary: tuple[str, float], korean: tuple[str, float]
) -> tuple[str, float, str]:
    """Choose a recognizer while favoring explicit Hangul and avoiding noise wins."""
    primary_text, primary_score = primary
    korean_text, korean_score = korean
    if contains_hangul(korean_text) and korean_score >= max(0.35, primary_score - 0.08):
        return korean_text, korean_score, "korean_PP-OCRv5_mobile_rec"
    if korean_score > primary_score + 0.08:
        return korean_text, korean_score, "korean_PP-OCRv5_mobile_rec"
    return primary_text, primary_score, "PP-OCRv5_mobile_rec"


def sort_reading_order(lines: Iterable[OcrLine]) -> list[OcrLine]:
    source = list(lines)
    if not source:
        return []
    median_height = sorted(line.bounds.height for line in source)[len(source) // 2]
    tolerance = max(6, round(median_height * 0.55))
    rows: list[list[OcrLine]] = []
    for line in sorted(source, key=lambda item: (item.bounds.y, item.bounds.x)):
        for row in rows:
            anchor = sum(item.bounds.y for item in row) / len(row)
            if abs(line.bounds.y - anchor) <= tolerance:
                row.append(line)
                break
        else:
            rows.append([line])
    ordered: list[OcrLine] = []
    for row in sorted(rows, key=lambda items: min(item.bounds.y for item in items)):
        ordered.extend(sorted(row, key=lambda item: item.bounds.x))
    return ordered


def join_lines(lines: Iterable[OcrLine]) -> str:
    ordered = sort_reading_order(lines)
    if not ordered:
        return ""
    output: list[str] = []
    current: list[OcrLine] = []
    median_height = sorted(line.bounds.height for line in ordered)[len(ordered) // 2]
    tolerance = max(6, round(median_height * 0.55))
    row_y: float | None = None
    for line in ordered:
        if row_y is None or abs(line.bounds.y - row_y) <= tolerance:
            current.append(line)
            row_y = sum(item.bounds.y for item in current) / len(current)
        else:
            output.append(" ".join(item.text.strip() for item in current if item.text.strip()))
            current = [line]
            row_y = float(line.bounds.y)
    if current:
        output.append(" ".join(item.text.strip() for item in current if item.text.strip()))
    return "\n".join(part for part in output if part)

