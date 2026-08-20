from __future__ import annotations

import json
from types import SimpleNamespace

from screen_ocr.app import run_ocr_diagnostic


def test_ocr_diagnostic_writes_machine_readable_result(tmp_path, monkeypatch) -> None:
    class FakeEngine:
        def recognize(self, image):
            assert image.shape == (220, 900, 3)
            return SimpleNamespace(
                text="Screen OCR Test 12345",
                lines=[object()],
                elapsed_ms=12,
                error=None,
            )

    monkeypatch.setattr("screen_ocr.app.PaddleOcrEngine", FakeEngine)
    output = tmp_path / "diagnostic.json"

    assert run_ocr_diagnostic(str(output)) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["ok"] is True
