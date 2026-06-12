"""Orchestrate the insight Railtracks flow and shape the result."""

from __future__ import annotations

from datetime import datetime, timezone

import railtracks as rt

from daily_insight.agents import build_insight_agent
from daily_insight.models import DailyInsight
from daily_insight.repositories import MetricRepository


PROMPT = (
    "Summarize the current metric data. Call get_recent_metrics(limit=50), "
    "then produce the strict per-metric output described in your system prompt."
)


def _result_text(result: object) -> str:
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)


class InsightService:
    """Run the daily insight agent and return a DailyInsight."""

    async def run(self) -> DailyInsight:
        agent_cls = build_insight_agent()
        flow = rt.Flow(name="DailyInsight", entry_point=agent_cls)
        result = await flow.ainvoke(PROMPT)

        text = _result_text(result).strip()
        metric_count = await _count_metrics()

        return DailyInsight(
            text=text,
            generated_at=datetime.now(timezone.utc),
            metric_count=metric_count,
        )


async def _count_metrics() -> int:
    """Cheap second read for the API response — does not block the agent."""
    try:
        records = await MetricRepository().list_recent(limit=50)
        return len({r.metric for r in records})
    except Exception:
        return 0
