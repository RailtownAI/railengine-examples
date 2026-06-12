"""Daily insight result shape returned to API callers."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DailyInsight(BaseModel):
    """One-line-per-metric plain-text summary of recent engine data."""

    text: str
    generated_at: datetime
    metric_count: int
    error: Optional[str] = None
