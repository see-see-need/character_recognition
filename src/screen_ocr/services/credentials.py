from __future__ import annotations

from typing import Protocol


class CredentialStore(Protocol):
    """Future provider secrets live here, never in QSettings."""

    def get(self, provider: str) -> str | None: ...

    def set(self, provider: str, secret: str) -> None: ...

    def delete(self, provider: str) -> None: ...

