"""FastAPI service that runs the daily insight agent on demand.

Run::

    uv run uvicorn daily_insight.controllers.api:app --reload --port 8000

Endpoints:
- GET  /health  — liveness probe
- POST /insight — run the Railtracks agent against Railengine and return a DailyInsight
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from daily_insight.config import (
    MissingEnvVarsError,
    ensure_dotenv_loaded,
    validate_required_env,
)
from daily_insight.models import DailyInsight
from daily_insight.services import InsightService


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dotenv_loaded()
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/insight", response_model=DailyInsight)
async def generate_insight() -> DailyInsight:
    try:
        return await InsightService().run()
    except Exception as exc:
        logger.exception("Failed to generate daily insight")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
