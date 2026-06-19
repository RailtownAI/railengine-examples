"""FastAPI service that runs the daily insight agent on demand.

Run::

    uv run uvicorn daily_insight.controllers.api:app --reload --port 8000

Endpoints:
- GET  /health   — liveness probe
- POST /insight  — run the Railtracks agent against Railengine and return a DailyInsight
- POST /evals/run — run the agent N times (or fetch a historical session), evaluate, return scores
"""

from __future__ import annotations

import logging
import os
from typing import Optional
from uuid import UUID

import railtownai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict, Field, model_validator

from daily_insight.config import (
    MissingEnvVarsError,
    configure_runtime_env,
    ensure_dotenv_loaded,
    validate_required_env,
)
from daily_insight.models import DailyInsight, EvaluationRun
from daily_insight.services import EvaluationService, InsightService


class EvaluateRequest(BaseModel):
    # extra="forbid" rejects typo'd keys at 422 instead of silently dropping
    # them — the old singular agent_run_id would otherwise slip through and
    # quietly trigger a Fresh-mode generation run.
    model_config = ConfigDict(extra="forbid")

    sample_size: int = Field(
        default=1,
        ge=1,
        le=5,
        description=(
            "Fresh-mode only. Number of fresh insight runs to generate and "
            "evaluate (capped at 5). Mutually exclusive with agent_run_ids."
        ),
    )
    agent_run_ids: Optional[list[UUID]] = Field(
        default=None,
        min_length=1,
        max_length=10,
        description=(
            "Historical-mode only. When set, fetches the named historical "
            "agent runs from Conductr (via railtownai.get_agent_runs) and "
            "evaluates those sessions as a single batch instead of generating "
            "fresh ones. Mutually exclusive with sample_size. Requires "
            "CONDUCTR_PROJECT_PAT and CONDUCTR_PROJECT_ID on the agent."
        ),
    )

    @model_validator(mode="after")
    def _enforce_mode_xor(self) -> "EvaluateRequest":
        """Reject bodies that try to drive both modes at once.

        Uses model_fields_set so the default sample_size=1 doesn't count as
        "set" — a caller passing only agent_run_ids still validates cleanly.
        """
        if (
            "sample_size" in self.model_fields_set
            and "agent_run_ids" in self.model_fields_set
        ):
            raise ValueError(
                "sample_size and agent_run_ids are mutually exclusive — "
                "omit sample_size when targeting historical runs."
            )
        return self


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dotenv_loaded()
    configure_runtime_env()

    # Wire Railtown observability when configured. railtownai.init attaches a
    # logging handler to the root logger, so any logger.exception/error call
    # downstream ships to Railtown automatically.
    if railtown_key := os.environ.get("RAILTOWN_API_KEY", "").strip():
        railtownai.init(railtown_key)
        logger.info("Railtown observability enabled")
    else:
        logger.info("RAILTOWN_API_KEY not set — Railtown observability disabled")

    try:
        validate_required_env()
    except MissingEnvVarsError as exc:
        logger.error(str(exc))
        raise
    yield


app = FastAPI(
    title="Daily Insight",
    description="Railtracks-powered status-page insight over Railengine metrics.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions.

    Logs the full traceback via Python's logging (Railtown's handler ships
    it onward when initialized) and returns a JSON 500 body with the
    exception type and message — far more useful than FastAPI's default
    plain-text "Internal Server Error" for diagnosing live failures.
    """
    logger.exception(
        "Unhandled exception in %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "type": type(exc).__name__,
            "detail": str(exc),
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/insight", response_model=DailyInsight)
async def generate_insight() -> DailyInsight:
    return await InsightService().run()


@app.post("/evals/run", response_model=EvaluationRun)
async def run_evaluation(req: EvaluateRequest = EvaluateRequest()) -> EvaluationRun:
    """Evaluate either fresh insight runs or one or more named historical runs.

    Fresh mode (``agent_run_ids`` absent): generates ``sample_size`` insight
    runs and scores them. Cost ≈ ``sample_size · 3`` LLM calls (1 to generate,
    2 for the FormatCompliance + FactualGrounding judge metrics).

    Historical mode (``agent_run_ids`` set): fetches the named sessions from
    Conductr and scores them as a single batch. Cost ≈ ``N · 2`` LLM calls
    (judge only). Requires ``CONDUCTR_PROJECT_PAT`` and ``CONDUCTR_PROJECT_ID``
    on the agent.

    ``ToolUseEvaluator`` and ``LLMInferenceEvaluator`` are free local checks in
    either mode.
    """
    return await EvaluationService().run(
        sample_size=req.sample_size,
        agent_run_ids=req.agent_run_ids,
    )
