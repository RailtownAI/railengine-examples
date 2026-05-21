"""Process-wide Railengine client for tool nodes (set from CLI before agent run)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from railtown.engine import Railengine

_client: Railengine | None = None


def set_railengine_client(client: Railengine) -> None:
    global _client
    _client = client


def get_railengine_client() -> Railengine:
    if _client is None:
        raise RuntimeError(
            "Railengine client is not configured. Call set_railengine_client() before invoking tools."
        )
    return _client
