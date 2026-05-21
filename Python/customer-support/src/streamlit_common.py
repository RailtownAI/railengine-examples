"""Shared Streamlit helpers: paths, fixtures, env status."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "tickets"


def env_ok() -> dict[str, bool]:
    return {
        "ENGINE_TOKEN": bool(os.environ.get("ENGINE_TOKEN", "").strip()),
        "ENGINE_PAT": bool(os.environ.get("ENGINE_PAT", "").strip()),
        "ENGINE_ID": bool(os.environ.get("ENGINE_ID", "").strip()),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
    }


def fixture_paths() -> list[Path]:
    if not FIXTURES_DIR.is_dir():
        return []
    return sorted(FIXTURES_DIR.glob("*.json"))


def render_env_metrics() -> None:
    """Render four env flags (values never shown)."""
    status = env_ok()
    cols = st.columns(4)
    for i, (key, ok) in enumerate(status.items()):
        cols[i].metric(label=key, value="set" if ok else "missing")
