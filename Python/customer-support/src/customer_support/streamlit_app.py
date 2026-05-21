"""Streamlit UI: edit ticket JSON, ingest, and triage."""

from __future__ import annotations

import asyncio
import json
import os
import traceback
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from customer_support._env import ensure_dotenv_loaded
from customer_support.ingest import ingest_ticket
from customer_support.models import SupportTicket, TriageAssessment
from customer_support.triage_runner import triage_ticket

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "tickets"


def _env_ok() -> dict[str, bool]:
    return {
        "ENGINE_TOKEN": bool(os.environ.get("ENGINE_TOKEN", "").strip()),
        "ENGINE_PAT": bool(os.environ.get("ENGINE_PAT", "").strip()),
        "ENGINE_ID": bool(os.environ.get("ENGINE_ID", "").strip()),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
    }


def _fixture_paths() -> list[Path]:
    if not FIXTURES_DIR.is_dir():
        return []
    return sorted(FIXTURES_DIR.glob("*.json"))


def main() -> None:
    ensure_dotenv_loaded()

    st.set_page_config(page_title="Support Triage", layout="wide")
    st.title("Customer support triage")
    st.caption("Railengine ingest + retrieval + Railtracks structured triage.")

    cols = st.columns(4)
    status = _env_ok()
    for i, (key, ok) in enumerate(status.items()):
        cols[i].metric(label=key, value="set" if ok else "missing")

    if "ticket_editor" not in st.session_state:
        st.session_state.ticket_editor = ""

    sidebar = st.sidebar
    sidebar.subheader("Fixtures")
    fixtures = _fixture_paths()
    fixture_names = [p.name for p in fixtures]

    if fixture_names:
        pick = sidebar.selectbox("Pick fixture file", fixture_names)
        if sidebar.button("Load into editor", type="secondary"):
            text = (FIXTURES_DIR / pick).read_text(encoding="utf-8")
            st.session_state.ticket_editor = text
            st.rerun()

    sidebar.caption(
        f"`fixtures/` path: `{FIXTURES_DIR}`"
        if fixtures
        else f"No `{FIXTURES_DIR}` — paste JSON manually."
    )

    txt = st.text_area(
        "Ticket JSON (`SupportTicket` schema)",
        height=340,
        key="ticket_editor",
    )

    c1, c2 = st.columns(2)

    ingest_ok = status["ENGINE_TOKEN"]

    ticket: SupportTicket | None = None
    if txt.strip():
        try:
            ticket = SupportTicket.model_validate(json.loads(txt))
            st.success("JSON matches `SupportTicket` schema.")
        except json.JSONDecodeError as e:
            st.warning(f"Invalid JSON: {e}")
        except ValidationError as e:
            st.error(f"Does not match `SupportTicket`: {e}")

    with c1:
        do_ingest = st.button(
            "Ingest to Railengine",
            disabled=not (ticket and ingest_ok),
            help="Requires ENGINE_TOKEN.",
        )

    triage_ready = (
        ticket
        and status["ENGINE_PAT"]
        and status["ENGINE_ID"]
        and status["OPENAI_API_KEY"]
    )

    with c2:
        do_triage = st.button(
            "Run triage",
            disabled=not triage_ready,
            help="Requires ENGINE_PAT, ENGINE_ID, and OPENAI_API_KEY.",
        )

    if do_ingest and ticket:
        try:
            with st.spinner("Ingesting…"):
                http_status = asyncio.run(ingest_ticket(ticket))
            st.success(f"Ingest succeeded (HTTP {http_status}).")
        except Exception:
            st.error(traceback.format_exc())

    if do_triage and ticket:
        try:
            with st.spinner("Running Railtracks triage (tools + structured output)…"):
                assessment = asyncio.run(triage_ticket(ticket))
            if not isinstance(assessment, TriageAssessment):
                assessment = TriageAssessment.model_validate(assessment)

            st.subheader("Triage output")
            m1, m2 = st.columns(2)
            m1.metric("Priority", assessment.priority.upper())
            m2.metric("Category", assessment.category)

            st.markdown("**Internal summary**")
            st.write(assessment.internal_summary)

            st.markdown("**Draft reply**")
            st.write(assessment.draft_reply_to_customer)

            st.markdown("**Reasoning**")
            st.write(assessment.reasoning)

            sid = assessment.similar_ticket_ids
            if sid:
                st.markdown("**Similar ticket ids**")
                st.code(", ".join(sid))

            raw = assessment.model_dump()
            st.download_button(
                label="Download TriageAssessment JSON",
                file_name=f"triage-{ticket.id}.json",
                mime="application/json",
                data=json.dumps(raw, indent=2, ensure_ascii=False).encode("utf-8"),
            )
            with st.expander("Full JSON"):
                st.json(raw)
        except Exception:
            st.error(traceback.format_exc())


if __name__ == "__main__":
    main()
