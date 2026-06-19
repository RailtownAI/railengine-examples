"""Evaluation run result returned by POST /evals/run."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from daily_insight.models.insight import DailyInsight


class EvaluationRun(BaseModel):
    """One end-to-end evaluation: N fresh insight runs plus their scores."""

    sample_size: int
    started_at: datetime
    completed_at: datetime
    insights: list[DailyInsight]
    evaluation_results: list[dict[str, Any]]
