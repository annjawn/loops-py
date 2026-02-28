from __future__ import annotations

from typing import Any


class LoopsError(Exception):
    """Base exception raised by loops-py."""


class LoopsAPIError(LoopsError):
    """Raised when Loops API returns an unsuccessful response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(f"Loops API error ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.response = response
        self.headers = headers or {}
