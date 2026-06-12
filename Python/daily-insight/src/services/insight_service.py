"""Orchestrate the insight Railtracks session and shape the result."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import railtracks as rt
import railtownai

from daily_insight.agents import build_insight_agent
from daily_insight.models import DailyInsight
from daily_insight.repositories import MetricRepository


PROMPT = (
    "Summarize the current metric data. Call get_recent_metrics(limit=50), "
    "then produce the strict per-metric output described in your system prompt."
)

_SESSION_NAME = "daily-insight-session"
_FLOW_NAME = "daily-insight"
_FLOW_ID = "daily-insight-agent"


logger = logging.getLogger(__name__)


def _result_text(result: object) -> str:
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)


def _upload_session(session: "rt.Session") -> None:
    """Upload the Railtracks session payload to Conductr when configured.

    Skips silently when ``railtownai.init`` hasn't run (no RAILTOWN_API_KEY),
    so a local invocation without observability still succeeds.
    """
    if railtownai.get_railtown_handler() is None:
        return
    try:
        success = railtownai.upload_agent_run(session.payload())
        logger.info("Agent run uploaded to Conductr: %s", success)
    except RuntimeError as exc:
        logger.warning("Skipping Railtown upload: %s", exc)
    except Exception:
        logger.exception("Unexpected error uploading agent run to Railtown")


class InsightService:
    """Run the daily insight agent and return a DailyInsight."""

    async def run(self) -> DailyInsight:
        agent_cls = build_insight_agent()
        message_history = rt.llm.MessageHistory([rt.llm.UserMessage(PROMPT)])

        with rt.Session(
            name=_SESSION_NAME,
            flow_name=_FLOW_NAME,
            flow_id=_FLOW_ID,
        ) as session:
            result = await rt.call(agent_cls, message_history)
            _upload_session(session)

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
