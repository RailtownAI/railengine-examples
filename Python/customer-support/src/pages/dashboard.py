"""Dashboard: interactive Kanban from full storage snapshot."""

from __future__ import annotations

import asyncio
import traceback

import streamlit as st

from customer_support.models.ticket import KANBAN_COLUMNS, TicketStatus, SupportTicket
from customer_support.services.ingest_service import IngestService
from customer_support.services.ticket_list_service import TicketListService
from customer_support.streamlit_common import (
    env_ok,
    group_tickets_by_status,
    render_app_toolbar,
    render_kanban_ticket_card,
    render_page_brand,
)

_KANBAN_SESSION_KEY = "kanban_tickets"
_KANBAN_INITIAL_LOAD_DONE = "kanban_initial_load_done"

render_page_brand()
refresh = render_app_toolbar(show_refresh_board=True)

st.title("Dashboard")
env = env_ok()
list_ready = env["ENGINE_PAT"] and env["ENGINE_ID"]
ingest_ready = env["ENGINE_TOKEN"]

if _KANBAN_SESSION_KEY not in st.session_state:
    st.session_state[_KANBAN_SESSION_KEY] = []

if not list_ready:
    st.warning(
        "Set **ENGINE_PAT** and **ENGINE_ID** to load tickets from Railengine.",
    )

if not ingest_ready:
    st.warning(
        "Set **ENGINE_TOKEN** to change status from card dropdowns (updates use ingest upsert)."
    )

should_load = list_ready and (
    refresh or not st.session_state.get(_KANBAN_INITIAL_LOAD_DONE)
)
if should_load:
    try:
        with st.spinner("Loading tickets from storage…"):
            st.session_state[_KANBAN_SESSION_KEY] = asyncio.run(
                TicketListService().fetch_all()
            )
        st.session_state[_KANBAN_INITIAL_LOAD_DONE] = True
    except Exception:
        st.error(traceback.format_exc())
    else:
        if refresh:
            st.success(f"Loaded **{len(st.session_state[_KANBAN_SESSION_KEY])}** tickets.")

tickets: list[SupportTicket] = st.session_state[_KANBAN_SESSION_KEY]
buckets = group_tickets_by_status(tickets)

cols = st.columns(4)

move_hit: tuple[SupportTicket, TicketStatus] | None = None

for idx, (_label, stat) in enumerate(KANBAN_COLUMNS):
    with cols[idx]:
        cnt = len(buckets[stat])
        st.markdown(f"#### {_label}  ")
        st.caption(f"{cnt} ticket(s)")
        for ticket in buckets[stat]:
            target = render_kanban_ticket_card(
                ticket,
                moves_disabled=not ingest_ready,
            )
            if target is not None:
                move_hit = (ticket, target)

if move_hit is not None and ingest_ready:
    tk, dest = move_hit
    svc = IngestService()
    try:
        with st.spinner("Updating status…"):
            status_code = asyncio.run(svc.update_status(tk, dest))
        if list_ready:
            st.session_state[_KANBAN_SESSION_KEY] = asyncio.run(
                TicketListService().fetch_all()
            )
        else:
            st.session_state[_KANBAN_SESSION_KEY] = [
                t.model_copy(update={"status": dest}) if t.id == tk.id else t
                for t in st.session_state[_KANBAN_SESSION_KEY]
            ]
        st.toast(f"Moved `{tk.id}` → **{dest}** (HTTP {status_code})", icon="✅")
        st.rerun()
    except Exception:
        st.error(traceback.format_exc())

if tickets:
    with st.expander("Table view"):
        tf = [
            {
                "id": t.id,
                "subject": t.subject[:140] + ("…" if len(t.subject) > 140 else ""),
                "status": t.status,
                "tags": ", ".join(t.tags),
                "productArea": t.productArea,
                "createdAt": t.createdAt,
            }
            for t in tickets
        ]
        st.dataframe(tf, hide_index=True, use_container_width=True)
