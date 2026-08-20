from screen_ocr.core.models import OcrLine, Rect
from screen_ocr.core.text import choose_recognition, join_lines, sort_reading_order


def line(text: str, x: int, y: int, confidence: float = 0.9) -> OcrLine:
    return OcrLine(text, Rect(x, y, 50, 18), confidence, "test")


def test_reading_order_groups_rows_then_x() -> None:
    values = [line("B", 80, 10), line("C", 10, 45), line("A", 10, 12)]
    assert [item.text for item in sort_reading_order(values)] == ["A", "B", "C"]
    assert join_lines(values) == "A B\nC"


def test_hangul_wins_when_confidence_is_close() -> None:
    selected = choose_recognition(("馥", 0.91), ("한글", 0.86))
    assert selected == ("한글", 0.86, "korean_PP-OCRv5_mobile_rec")


def test_primary_has_noise_margin() -> None:
    selected = choose_recognition(("Hello", 0.85), ("HeIIo", 0.89))
    assert selected[0] == "Hello"

