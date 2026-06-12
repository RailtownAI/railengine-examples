"""Load `.env` and validate required environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


REQUIRED_ENV_VARS = ("ENGINE_PAT", "ENGINE_ID", "ANTHROPIC_API_KEY")


class MissingEnvVarsError(RuntimeError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        names = ", ".join(missing)
        super().__init__(
            f"Missing required environment variables: {names}. "
            f"Set them in .env (see .env.example)."
        )


def ensure_dotenv_loaded() -> None:
    """Load env from `Python/daily-insight/.env`, then cwd `.env` (override)."""
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    load_dotenv()


def validate_required_env() -> None:
    """Raise MissingEnvVarsError if any required variable is unset or blank."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name, "").strip()]
    if missing:
        raise MissingEnvVarsError(missing)
