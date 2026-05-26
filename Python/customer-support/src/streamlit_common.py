"""Shared Streamlit helpers: paths, fixtures, env status."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

import streamlit as st

from customer_support.models.ticket import (
    KANBAN_COLUMNS,
    TICKET_STATUSES,
    TicketStatus,
    SupportTicket,
)
from customer_support.models.triage import TriageAssessment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "tickets"
BRAND_LOGO_PATH = PROJECT_ROOT / "assets" / "logo-railengine.png"

PRIORITY_ORDER = {"p1": 0, "p2": 1, "p3": 2, "p4": 3}

TICKET_ID_PATTERN = re.compile(r"\b(ticket-[a-zA-Z0-9-]+)\b")


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


_PIPELINE_STAGES_HTML = """
<style>
  .re-pipeline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: nowrap;
    width: 100%;
    box-sizing: border-box;
    gap: 0.15rem;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 0.8rem;
    margin: 0.25rem 0 0.5rem;
  }
  .re-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1 1 0;
    min-width: 4.5rem;
    text-align: center;
  }
  .re-icon {
    width: 2.75rem;
    height: 2.75rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    color: #fff;
    margin-bottom: 0.35rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
  }
  .re-title { font-weight: 600; color: #31333f; line-height: 1.2; }
  .re-sub { font-size: 0.68rem; color: #808495; line-height: 1.15; margin-top: 0.1rem; }
  .re-arrow { color: #c4c4c4; font-size: 1.25rem; padding: 0 0.1rem; margin-bottom: 1.4rem; }
  .re-stage.inactive .re-icon { background: #e8e8ed !important; color: #a3a3ac; }
  .re-stage.inactive .re-title, .re-stage.inactive .re-sub { color: #a3a3ac; }
</style>
<div class="re-pipeline" role="img" aria-label="Railengine pipeline stages">
  <div class="re-stage">
    <div class="re-icon" style="background:#2563eb">📄</div>
    <div class="re-title">Ingest</div>
    <div class="re-sub">JSON Documents</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage">
    <div class="re-icon" style="background:#9f1239">🎭</div>
    <div class="re-title">Masking</div>
    <div class="re-sub">Remove Sensitive Data</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage">
    <div class="re-icon" style="background:#0284c7">📦</div>
    <div class="re-title">Cold Storage</div>
    <div class="re-sub">Backup Data</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage">
    <div class="re-icon" style="background:#7c3aed">🔗</div>
    <div class="re-title">Embedding</div>
    <div class="re-sub">Vector Search</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage">
    <div class="re-icon" style="background:#ca8a04">🔍</div>
    <div class="re-title">Indexing</div>
    <div class="re-sub">Text Search</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage">
    <div class="re-icon" style="background:#ea580c">🗄️</div>
    <div class="re-title">Hot Storage</div>
    <div class="re-sub">Retrieve Document</div>
  </div>
  <div class="re-arrow">→</div>
  <div class="re-stage inactive">
    <div class="re-icon">📣</div>
    <div class="re-title">Publishing</div>
    <div class="re-sub">Send notification</div>
  </div>
</div>
"""


_FULL_WIDTH_CSS = """
<style>
  section.main > div.block-container {
    max-width: 100%;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
  div[data-testid="stHtml"] {
    width: 100%;
  }
  div[data-testid="stHtml"] iframe {
    width: 100% !important;
  }
  /* Ticket subject buttons (tertiary): full width, left-aligned label */
  section.main .element-container:has(button[data-testid="baseButton-tertiary"]) {
    width: 100%;
    align-self: stretch;
  }
  section.main div[data-testid="stButton"]:has(button[data-testid="baseButton-tertiary"]) {
    width: 100%;
    display: flex;
    justify-content: flex-start;
    align-self: stretch;
  }
  section.main button[data-testid="baseButton-tertiary"] {
    width: 100% !important;
    max-width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding-left: 0 !important;
  }
  section.main button[data-testid="baseButton-tertiary"] > div {
    justify-content: flex-start !important;
    width: 100%;
  }
  section.main button[data-testid="baseButton-tertiary"] p {
    text-align: left !important;
    width: 100%;
  }
</style>
"""


def use_full_width_layout() -> None:
    """Expand main content to full viewport width (call once from app entry)."""
    st.markdown(_FULL_WIDTH_CSS, unsafe_allow_html=True)


def render_page_brand() -> None:
    """Clickable Railengine logo at the top of the main content area."""
    if not BRAND_LOGO_PATH.is_file():
        return
    b64 = base64.b64encode(BRAND_LOGO_PATH.read_bytes()).decode()
    st.markdown(
        f'<a href="https://railengine.ai" target="_blank" rel="noopener" '
        f'style="display:inline-block;margin-bottom:0.25rem;">'
        f'<img src="data:image/png;base64,{b64}" alt="Railengine" width="120" '
        f'style="display:inline-block;vertical-align:middle;"/></a>',
        unsafe_allow_html=True,
    )


def render_pipeline_stages() -> None:
    """Railengine pipeline overview (HTML; works without Mermaid support)."""
    st.markdown("#### Pipeline stages")
    st.html(_PIPELINE_STAGES_HTML, width="stretch")
    st.caption(
        "This page sends JSON through **Ingest**. Triage agents search **Embedding** and "
        "**Indexing**; the dashboard reads **Hot Storage**; **Search** queries the index."
    )


@st.dialog("Config")
def show_env_config_dialog() -> None:
    """Modal: which env vars are set (values never shown)."""
    st.caption(
        "Loaded from `.env` next to `pyproject.toml`. Secret values are not displayed."
    )
    status = env_ok()
    cols = st.columns(4)
    for i, (key, ok) in enumerate(status.items()):
        cols[i].metric(label=key, value="set" if ok else "missing")


def render_app_toolbar(*, show_refresh_board: bool = False) -> bool:
    """Top-right toolbar: optional **Refresh board** + **Config** (same row)."""
    refresh_clicked = False
    if show_refresh_board:
        _, refresh_col, config_col = st.columns([9, 1, 1])
        with refresh_col:
            refresh_clicked = st.button(
                "🔄 Refresh",
                type="secondary",
                use_container_width=True,
            )
    else:
        _, config_col = st.columns([11, 1])

    with config_col:
        if st.button("⚙️ Config", type="secondary", use_container_width=True):
            show_env_config_dialog()

    return refresh_clicked


def group_tickets_by_status(
    tickets: list[SupportTicket],
) -> dict[TicketStatus, list[SupportTicket]]:
    buckets: dict[TicketStatus, list[SupportTicket]] = {s: [] for s in TICKET_STATUSES}
    for t in tickets:
        buckets[t.status].append(t)
    return buckets


@st.dialog("Ticket details", width="large")
def show_ticket_details_dialog(ticket: SupportTicket) -> None:
    """Modal with full ticket fields (read-only)."""
    st.markdown(f"### {ticket.subject}")

    m1, m2, m3 = st.columns(3)
    status_label = next(
        (label for label, stat in KANBAN_COLUMNS if stat == ticket.status),
        ticket.status,
    )
    m1.metric("Status", status_label)
    m2.metric("Product area", ticket.productArea or "—")
    m3.metric("Created", ticket.createdAt[:10] if ticket.createdAt else "—")

    st.markdown("**Ticket ID**")
    st.code(ticket.id)

    if ticket.tags:
        st.markdown("**Tags**")
        st.write(", ".join(ticket.tags))

    if ticket.customerEmail or ticket.customerPhone:
        st.markdown("**Customer**")
        if ticket.customerEmail:
            st.write(f"Email: `{ticket.customerEmail}`")
        if ticket.customerPhone:
            st.write(f"Phone: `{ticket.customerPhone}`")

    st.markdown("**Body**")
    st.text_area(
        "Body",
        value=ticket.body,
        height=220,
        disabled=True,
        label_visibility="collapsed",
    )

    with st.expander("Raw JSON"):
        st.json(ticket.model_dump())


def render_chat_message_with_ticket_links(
    content: str,
    tickets_by_id: dict[str, SupportTicket],
    *,
    message_index: int,
) -> None:
    """Render assistant text; link ticket ids mentioned in the response."""
    st.markdown(content)
    mentioned = list(dict.fromkeys(TICKET_ID_PATTERN.findall(content)))
    linked = [tid for tid in mentioned if tid in tickets_by_id]
    if not linked:
        return
    st.caption("Tickets in this reply (click subject for details):")
    for tid in linked:
        render_ticket_subject_button(
            tickets_by_id[tid],
            key=f"chat_msg:{message_index}:{tid}",
        )


def render_ticket_subject_button(ticket: SupportTicket, *, key: str) -> None:
    """Tertiary button on the ticket subject; opens ``show_ticket_details_dialog``."""
    subj = ticket.subject[:100] + ("…" if len(ticket.subject) > 100 else "")
    if st.button(
        f"🎫 {subj}",
        key=key,
        width="stretch",
        type="tertiary",
    ):
        show_ticket_details_dialog(ticket)


def render_kanban_ticket_card(
    ticket: SupportTicket,
    *,
    moves_disabled: bool,
) -> TicketStatus | None:
    """
    One Kanban card with a status dropdown and a dialog trigger on the subject.
    Returns the new status when the selection differs from the ticket's current status.
    """
    labels = [label for label, _ in KANBAN_COLUMNS]
    status_by_label = {label: stat for label, stat in KANBAN_COLUMNS}
    index = next(i for i, (_, s) in enumerate(KANBAN_COLUMNS) if s == ticket.status)

    with st.container(border=True):
        render_ticket_subject_button(ticket, key=f"view:{ticket.id}")
        tags = ", ".join(ticket.tags[:6])
        st.caption(f"`{ticket.id}` · _{ticket.productArea}_ · {ticket.createdAt[:10]}")
        if tags:
            st.caption(tags)
        selected_label = st.selectbox(
            "Status",
            options=labels,
            index=index,
            key=f"status:{ticket.id}",
            disabled=moves_disabled,
            label_visibility="collapsed",
        )

    selected = status_by_label[selected_label]
    if selected != ticket.status:
        return selected
    return None


def render_triage_assessment(
    ticket: SupportTicket, assessment: TriageAssessment
) -> None:
    """Display structured triage output for a single ticket."""
    with st.container(border=True):
        render_ticket_subject_button(ticket, key=f"triage_result_view:{ticket.id}")
        st.caption(f"`{ticket.id}` · queue status: **{ticket.status}**")
        m1, m2 = st.columns(2)
        m1.metric("Priority", assessment.priority.upper())
        m2.metric("Category", assessment.category)
        st.markdown("**Why work on this**")
        st.write(assessment.reasoning)
        st.markdown("**Internal summary**")
        st.write(assessment.internal_summary)
        if assessment.similar_ticket_ids:
            st.caption(f"Similar tickets: {', '.join(assessment.similar_ticket_ids)}")
        with st.expander("Draft reply & full JSON"):
            st.markdown("**Draft reply**")
            st.write(assessment.draft_reply_to_customer)
            st.json(assessment.model_dump())
