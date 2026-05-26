"""Load `.env` before reading Railengine / LLM environment variables."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def ensure_dotenv_loaded() -> None:
    """
    Load env from `Python/customer-support/.env`, then cwd `.env` (override).
    """
    # ``src/config/env.py`` → parents[2] == customer-support project root
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    load_dotenv()
