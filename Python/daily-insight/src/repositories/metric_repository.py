"""Railengine retrieval for MetricRecord documents."""

from __future__ import annotations

from typing import Any

from railtown.engine import Railengine

from daily_insight.models import MetricRecord


def _as_metric(item: Any) -> MetricRecord | None:
    if isinstance(item, MetricRecord):
        return item
    if isinstance(item, dict):
        try:
            return MetricRecord.model_validate(item)
        except Exception:
            return None
    return None


class MetricRepository:
    """Single-page reads against the Railengine storage API."""

    async def list_recent(self, limit: int = 50) -> list[MetricRecord]:
        """Return up to ``limit`` metric records from the most recent page.

        ``page_size`` is capped at 100 by the SDK; callers wanting more should
        page through ``list_storage_documents`` directly.
        """
        page_size = max(1, min(int(limit), 100))
        async with Railengine(model=MetricRecord) as client:
            page = await client.list_storage_documents(
                page_number=1,
                page_size=page_size,
            )

        out: list[MetricRecord] = []
        for item in page.items:
            metric = _as_metric(item)
            if metric is not None:
                out.append(metric)
        return out
