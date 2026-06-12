"""Generate fresh insight runs (or fetch a historical run) and evaluate them."""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

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


def _fetch_historical_session(agent_run_id: UUID) -> dict[str, Any]:
    """Fetch a session payload from Conductr via railtownai.get_agent_runs.

    Returns the nested session shape (session_id, runs: [...]) that
    extract_agent_data_points consumes. Raises whatever the SDK raises —
    AgentRunsNotInitializedError when CONDUCTR_PROJECT_PAT/CONDUCTR_PROJECT_ID
    aren't set, AgentRunFetchError on HTTP/parse failures — and the global
    exception handler shapes those into a 500 JSON body.
    """
    payloads = railtownai.get_agent_runs([str(agent_run_id)])
    if not payloads:
        raise RuntimeError(
            f"Conductr returned no payload for agent_run_id={agent_run_id}"
        )
    return payloads[0]


class EvaluationService:
    """Generate or fetch insight session(s) and evaluate them.

    Two modes:
    - **Fresh** (default) — generate ``sample_size`` insight runs via
      ``InsightService.run_and_capture_session`` and evaluate them.
    - **Historical** — when ``agent_run_id`` is provided, fetch that specific
      run from Conductr via ``railtownai.get_agent_runs`` and evaluate only
      that session. ``sample_size`` is ignored in this mode.
    """

    async def run(
        self,
        sample_size: int = 1,
        agent_run_id: UUID | None = None,
    ) -> EvaluationRun:
        started_at = datetime.now(timezone.utc)

        if agent_run_id is not None:
            logger.info("Evaluating historical session agent_run_id=%s", agent_run_id)
            session_payloads: list[dict[str, Any]] = [
                _fetch_historical_session(agent_run_id)
            ]
            insights: list[DailyInsight] = []
            effective_sample_size = 1
        else:
            effective_sample_size = max(1, min(int(sample_size), _MAX_SAMPLE_SIZE))
            insight_service = InsightService()
            insights = []
            session_payloads = []
            for i in range(effective_sample_size):
                logger.info(
                    "Generating insight run %s/%s", i + 1, effective_sample_size
                )
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
            logger.info(
                "Extracted %s agent data points from %s session(s)",
                len(data),
                len(session_files),
            )

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
            sample_size=effective_sample_size,
            started_at=started_at,
            completed_at=completed_at,
            insights=insights,
            evaluation_results=[r.model_dump(mode="json") for r in evaluation_results],
        )
