from __future__ import annotations

import os

import pytest


# A QApplication must be the first Qt application created in the test process.
# test_single_instance also works with QCoreApplication, but creating that first
# makes Qt abort when the later UI tests construct their first widget.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qt_application() -> QApplication:
    app = QApplication.instance() or QApplication([])
    yield app
