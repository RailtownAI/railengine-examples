"""Generate fresh insight runs and evaluate them with the configured evaluators."""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import railtownai
from railtracks import evaluations as evals

from daily_insight.agents.evaluations import build_evaluators
from daily_insight.models import DailyInsight, EvaluationRun
from daily_insight.services.insight_service import InsightService


logger = logging.getLogger(__name__)

_AGENT_NAME = "Daily Insight Agent"
_MAX_SAMPLE_SIZE = 5


def _upload_evaluation(payload: dict[str, Any]) -> None:
    """Callback handed to evals.evaluate — uploads each EvaluationResult to Conductr."""
    if railtownai.get_railtown_handler() is None:
        return
    try:
        railtownai.upload_agent_evaluation(payload)
        logger.info("Evaluation result uploaded to Conductr")
    except Exception:
        logger.exception("Failed to upload evaluation result to Railtown")


class EvaluationService:
    """Run N fresh insight invocations and evaluate them with the agent's evaluators."""

    async def run(self, sample_size: int = 1) -> EvaluationRun:
        sample_size = max(1, min(int(sample_size), _MAX_SAMPLE_SIZE))
        started_at = datetime.now(timezone.utc)

        insight_service = InsightService()
        insights: list[DailyInsight] = []
        session_payloads: list[dict[str, Any]] = []

        for i in range(sample_size):
            logger.info("Generating insight run %s/%s", i + 1, sample_size)
            insight, payload = await insight_service.run_and_capture_session()
            insights.append(insight)
            session_payloads.append(payload)

        # extract_agent_data_points reads JSON session files from disk. Stage the
        # captured payloads in a request-scoped tempdir so each /evaluate call
        # sees exactly its own sessions — no leakage between concurrent requests.
        with tempfile.TemporaryDirectory(prefix="daily-insight-eval-") as tmpdir:
            tmp = Path(tmpdir)
            session_files: list[str] = []
            for idx, payload in enumerate(session_payloads):
                fp = tmp / f"session_{idx}.json"
                fp.write_text(json.dumps(payload), encoding="utf-8")
                session_files.append(str(fp))

            data = evals.extract_agent_data_points(session_files)
            logger.info("Extracted %s agent data points from %s sessions", len(data), len(session_files))

            evaluation_name = f"daily-insight-{started_at.strftime('%Y%m%dT%H%M%SZ')}"

            # agent_selection=False + agents=[...] keeps evaluate() headless.
            # payload_callback fires once per EvaluationResult as it completes.
            evaluation_results = evals.evaluate(
                data=data,
                evaluators=build_evaluators(),
                agents=[_AGENT_NAME],
                agent_selection=False,
                name=evaluation_name,
                payload_callback=_upload_evaluation,
            )

        completed_at = datetime.now(timezone.utc)
        return EvaluationRun(
            sample_size=sample_size,
            started_at=started_at,
            completed_at=completed_at,
            insights=insights,
            evaluation_results=[r.model_dump(mode="json") for r in evaluation_results],
        )
