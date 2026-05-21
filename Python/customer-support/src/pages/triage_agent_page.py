"""Streamlit page: triage open and pending tickets with the Railtracks agent."""

from __future__ import annotations

import asyncio
import traceback

import streamlit as st

from customer_support.models import SupportTicket, TriageAssessment
from customer_support.services.ticket_list_service import TicketListService
from customer_support.services.triage_service import TriageService
from customer_support.streamlit_common import (
    PRIORITY_ORDER,
    env_ok,
    render_env_metrics,
    render_triage_assessment,
)

_QUEUE_KEY = "triage_agent_queue"
_RESULTS_KEY = "triage_agent_results"
_CHAT_KEY = "triage_agent_chat"

st.title("Triage Agent")
st.caption(
    "Chat with the triage lead on the left; load and run structured triage on **open** and **pending** "
    "tickets on the right."
)

render_env_metrics()

env = env_ok()
list_ready = env["ENGINE_PAT"] and env["ENGINE_ID"]
triage_ready = list_ready and env["OPENAI_API_KEY"]

if _QUEUE_KEY not in st.session_state:
    st.session_state[_QUEUE_KEY] = []
if _RESULTS_KEY not in st.session_state:
    st.session_state[_RESULTS_KEY] = {}
if _CHAT_KEY not in st.session_state:
    st.session_state[_CHAT_KEY] = []

if not list_ready:
    st.warning("Set **ENGINE_PAT** and **ENGINE_ID** to load the triage queue.")
if not env["OPENAI_API_KEY"]:
    st.warning("Set **OPENAI_API_KEY** to run the triage agent.")

chat_col, triage_col = st.columns([1, 1], gap="large")

with chat_col:
    st.subheader("Chat with agent")
    st.caption("Ask about the queue, priorities, or similar resolved tickets.")

    if st.button("Clear chat", type="secondary"):
        st.session_state[_CHAT_KEY] = []
        st.rerun()

    for msg in st.session_state[_CHAT_KEY]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    queue_snapshot: list[SupportTicket] = st.session_state[_QUEUE_KEY]
    if prompt := st.chat_input(
        "Ask the triage agent…",
        disabled=not triage_ready,
    ):
        st.session_state[_CHAT_KEY].append({"role": "user", "content": prompt})
        try:
            with st.spinner("Agent thinking…"):
                reply = asyncio.run(
                    TriageService().chat(
                        st.session_state[_CHAT_KEY],
                        queue=queue_snapshot or None,
                    )
                )
            st.session_state[_CHAT_KEY].append({"role": "assistant", "content": reply})
        except Exception:
            st.session_state[_CHAT_KEY].pop()
            st.error(traceback.format_exc())
        else:
            st.rerun()

with triage_col:
    toolbar = st.columns([2, 2])
    load_queue = toolbar[0].button("Load queue")
    triage_all = toolbar[1].button(
        "Triage queue",
        disabled=not triage_ready or len(st.session_state[_QUEUE_KEY]) == 0,
    )

    if load_queue and list_ready:
        try:
            with st.spinner("Loading open and pending tickets…"):
                st.session_state[_QUEUE_KEY] = asyncio.run(TicketListService().fetch_open_and_pending())
        except Exception:
            st.error(traceback.format_exc())
        else:
            n = len(st.session_state[_QUEUE_KEY])
            st.success(f"Queue loaded: **{n}** ticket(s) (open + pending).")

    queue: list[SupportTicket] = st.session_state[_QUEUE_KEY]
    results: dict[str, TriageAssessment] = st.session_state[_RESULTS_KEY]

    if triage_all and triage_ready and queue:
        try:
            progress = st.progress(0.0, text="Running triage agent…")

            async def _triage_queue() -> dict[str, TriageAssessment]:
                svc = TriageService()
                batch: dict[str, TriageAssessment] = {}
                total = len(queue)
                for i, ticket in enumerate(queue, start=1):
                    progress.progress(i / total, text=f"Triage {i}/{total}: {ticket.id}")
                    batch[ticket.id] = await svc.run(ticket)
                return batch

            batch = asyncio.run(_triage_queue())
            st.session_state[_RESULTS_KEY] = batch
            results = batch
            progress.empty()
            st.success(f"Triage complete for **{len(batch)}** ticket(s).")
        except Exception:
            st.error(traceback.format_exc())

    if queue:
        st.subheader("Queue")
        st.caption(f"{len(queue)} ticket(s) awaiting triage (open or pending).")
        for ticket in queue:
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(f"**{ticket.subject}**")
                st.caption(f"`{ticket.id}` · **{ticket.status}** · {ticket.productArea}")
            with cols[1]:
                if st.button(
                    "Triage",
                    key=f"triage_one:{ticket.id}",
                    disabled=not triage_ready,
                    use_container_width=True,
                ):
                    try:
                        with st.spinner(f"Triage {ticket.id}…"):
                            assessment = asyncio.run(TriageService().run(ticket))
                        st.session_state[_RESULTS_KEY][ticket.id] = assessment
                        st.rerun()
                    except Exception:
                        st.error(traceback.format_exc())
    else:
        st.info("Click **Load queue** to fetch open and pending tickets from storage.")

    if results:
        st.subheader("Triage results")
        st.caption("Sorted by priority (P1 first).")

        ticket_by_id = {t.id: t for t in queue}
        sorted_ids = sorted(
            results.keys(),
            key=lambda tid: (
                PRIORITY_ORDER.get(results[tid].priority, 99),
                tid,
            ),
        )

        for tid in sorted_ids:
            ticket = ticket_by_id.get(tid)
            if ticket is None:
                continue
            render_triage_assessment(ticket, results[tid])
