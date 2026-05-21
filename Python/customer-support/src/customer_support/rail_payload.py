"""Normalize Railengine storage/search rows into ticket-shaped dicts.

The HTTP API may expose user JSON under Body, body, content, or Content (string or object),
matching patterns used elsewhere in railengine-examples TypeScript helpers.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from customer_support.models import SupportTicket


def _parse_json_if_string(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return raw


def row_as_dict(row: Any) -> dict[str, Any] | None:
    """Coerce SDK hits (dict or Pydantic, e.g. vector rows) into a plain dict."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if isinstance(row, BaseModel):
        return row.model_dump(by_alias=True)
    return None


def body_from_row(row: Any) -> dict[str, Any] | None:
    """Extract the user document object from a storage or search row."""
    d = row_as_dict(row)
    if not d:
        return None
    raw = d.get("Body") or d.get("body") or d.get("content") or d.get("Content")
    parsed = _parse_json_if_string(raw)
    if isinstance(parsed, dict):
        return parsed
    # Row may already be the flat document (unlikely but tolerate)
    if "id" in d and "subject" in d:
        return dict(d)
    return None


def ticket_from_row(row: Any) -> SupportTicket | None:
    """Parse a storage/search hit into SupportTicket if possible."""
    if isinstance(row, SupportTicket):
        return row
    body = body_from_row(row)
    if not body:
        return None
    try:
        return SupportTicket.model_validate(body)
    except Exception:
        return None


def row_preview(row: Any, max_len: int = 400) -> str:
    """Short string for logging tool results."""
    t = ticket_from_row(row)
    if t:
        return f"{t.id} | {t.status} | {t.subject[:80]}"
    body = body_from_row(row)
    if body:
        s = json.dumps(body, ensure_ascii=False)[:max_len]
        return s + ("…" if len(s) == max_len else "")
    return str(row)[:max_len]
