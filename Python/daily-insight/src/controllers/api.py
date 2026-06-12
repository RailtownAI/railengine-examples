"""FastAPI service that runs the daily insight agent on demand.

Run::

    uv run uvicorn daily_insight.controllers.api:app --reload --port 8000

Endpoints:
- GET  /health   — liveness probe
- POST /insight  — run the Railtracks agent against Railengine and return a DailyInsight
- POST /evaluate — run the agent N times, evaluate the sessions, return scores
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
from pydantic import BaseModel, Field

from daily_insight.config import (
    MissingEnvVarsError,
    configure_runtime_env,
    ensure_dotenv_loaded,
    validate_required_env,
)
from daily_insight.models import DailyInsight, EvaluationRun
from daily_insight.services import EvaluationService, InsightService


class EvaluateRequest(BaseModel):
    sample_size: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of fresh insight runs to generate and evaluate (capped at 5).",
    )
    # Forward-compat: when populated, future versions will fetch the named
    # historical run from Conductr and evaluate that instead of generating
    # fresh runs. Currently accepted (so existing clients don't need updating
    # later) but logged + ignored — `sample_size` still drives behaviour.
    agent_run_id: Optional[UUID] = Field(
        default=None,
        description="Optional. Reserved for future use — will identify a specific historical agent run to evaluate. Currently logged and ignored; sample_size still drives behaviour.",
    )


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


@app.post("/evaluate", response_model=EvaluationRun)
async def evaluate(req: EvaluateRequest = EvaluateRequest()) -> EvaluationRun:
    """Run the agent N times and evaluate the resulting sessions.

    Cost per call ≈ ``sample_size · 3`` LLM calls — one to generate the insight,
    two for the judge metrics (FormatCompliance + FactualGrounding). The
    ToolUseEvaluator and LLMInferenceEvaluator are cost-free local checks.
    """
    if req.agent_run_id is not None:
        logger.info(
            "agent_run_id=%s provided but not yet wired — generating fresh runs",
            req.agent_run_id,
        )
    return await EvaluationService().run(sample_size=req.sample_size)
