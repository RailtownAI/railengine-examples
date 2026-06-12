"""Railtracks tool nodes backed by MetricRepository."""

from __future__ import annotations

import json

import railtracks as rt

from daily_insight.repositories import MetricRepository


@rt.function_node
async def get_recent_metrics(limit: int = 50) -> str:
    """
    Fetch the most recent metric records from Railengine.

    Args:
        limit: Maximum number of records to return (capped at 100 by the SDK).
    """
    repo = MetricRepository()
    records = await repo.list_recent(limit=limit)
    return json.dumps([r.model_dump() for r in records], ensure_ascii=False)
