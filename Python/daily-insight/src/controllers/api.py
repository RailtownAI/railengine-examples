"""FastAPI service that runs the daily insight agent on demand.

Run::

    uv run uvicorn daily_insight.controllers.api:app --reload --port 8000

Endpoints:
- GET  /health  — liveness probe
- POST /insight — run the Railtracks agent against Railengine and return a DailyInsight
"""

from __future__ import annotations

import logging
import os

import railtownai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from daily_insight.config import (
    MissingEnvVarsError,
    configure_runtime_env,
    ensure_dotenv_loaded,
    validate_required_env,
)
from daily_insight.models import DailyInsight
from daily_insight.services import InsightService


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
