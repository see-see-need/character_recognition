from screen_ocr.core.models import Rect, logical_to_pixel_rect


def test_logical_to_pixel_rect_covers_scaled_bounds() -> None:
    assert logical_to_pixel_rect(Rect(10, 20, 101, 51), 1.25) == Rect(12, 25, 127, 64)


def test_logical_to_pixel_rect_handles_zero_size() -> None:
    assert logical_to_pixel_rect(Rect(2, 3, 0, 0), 1.5) == Rect(3, 4, 0, 0)

