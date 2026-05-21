"""Shared Streamlit helpers: paths, fixtures, env status."""

from __future__ import annotations

import os
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

PRIORITY_ORDER = {"p1": 0, "p2": 1, "p3": 2, "p4": 3}


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


def render_env_metrics(*, expanded: bool = False) -> None:
    """Env flags in a collapsed expander (values never shown)."""
    with st.expander("Environment variables", expanded=expanded):
        status = env_ok()
        cols = st.columns(4)
        for i, (key, ok) in enumerate(status.items()):
            cols[i].metric(label=key, value="set" if ok else "missing")


def group_tickets_by_status(tickets: list[SupportTicket]) -> dict[TicketStatus, list[SupportTicket]]:
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
        subj = ticket.subject[:100] + ("…" if len(ticket.subject) > 100 else "")
        if st.button(
            subj,
            key=f"view:{ticket.id}",
            use_container_width=True,
            type="tertiary",
        ):
            show_ticket_details_dialog(ticket)
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


def render_triage_assessment(ticket: SupportTicket, assessment: TriageAssessment) -> None:
    """Display structured triage output for a single ticket."""
    with st.container(border=True):
        st.markdown(f"**{ticket.subject}**")
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
