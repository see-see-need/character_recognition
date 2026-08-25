from uuid import uuid4

from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QLocalServer

from screen_ocr import app as app_module


def test_second_instance_notifies_primary(monkeypatch) -> None:
    qt_app = QCoreApplication.instance() or QCoreApplication([])
    server_name = f"ScreenOCR.Test.{uuid4().hex}"
    monkeypatch.setattr(app_module, "SINGLE_INSTANCE_NAME", server_name)
    primary = app_module.SingleInstanceGuard()
    secondary = app_module.SingleInstanceGuard()
    activations = []
    primary.activation_requested.connect(lambda: activations.append(True))
    try:
        assert primary.start_primary() is True
        assert secondary.start_primary() is False
        qt_app.processEvents()
        assert activations == [True]
    finally:
        primary.close()
        secondary.close()
        QLocalServer.removeServer(server_name)
