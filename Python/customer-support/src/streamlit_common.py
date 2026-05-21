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


def group_tickets_by_status(tickets: list[SupportTicket]) -> dict[TicketStatus, list[SupportTicket]]:
    buckets: dict[TicketStatus, list[SupportTicket]] = {s: [] for s in TICKET_STATUSES}
    for t in tickets:
        buckets[t.status].append(t)
    return buckets


def render_kanban_ticket_card(
    ticket: SupportTicket,
    *,
    moves_disabled: bool,
) -> TicketStatus | None:
    """
    One Kanban card with a status dropdown.
    Returns the new status when the selection differs from the ticket's current status.
    """
    labels = [label for label, _ in KANBAN_COLUMNS]
    status_by_label = {label: stat for label, stat in KANBAN_COLUMNS}
    index = next(i for i, (_, s) in enumerate(KANBAN_COLUMNS) if s == ticket.status)

    with st.container(border=True):
        subj = ticket.subject[:100] + ("…" if len(ticket.subject) > 100 else "")
        st.markdown(f"**{subj}**")
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
