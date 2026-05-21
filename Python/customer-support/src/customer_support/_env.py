"""Load `.env` for CLI entrypoints before reading os.environ."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def ensure_dotenv_loaded() -> None:
    """
    Load env vars used by Railengine ingest/retrieval and LLMs.

    - First loads `Python/customer-support/.env` next to this package (works even when cwd is elsewhere).
    - Then `load_dotenv()` so a `.env` in the current working directory can override values.
    """
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
    load_dotenv()
