"""Streamlit page: Customer Support Agent (chat + structured triage)."""

from __future__ import annotations

import asyncio
import traceback

import streamlit as st

from customer_support.models import SupportTicket, TriageAssessment
from customer_support.repositories import TicketRepository
from customer_support.services.ticket_list_service import TicketListService
from customer_support.services.triage_service import TriageService
from customer_support.streamlit_common import (
    PRIORITY_ORDER,
    TICKET_ID_PATTERN,
    env_ok,
    render_chat_message_with_ticket_links,
    render_page_brand,
    render_ticket_subject_button,
    render_triage_assessment,
)

_QUEUE_KEY = "agent_queue"
_RESULTS_KEY = "agent_results"
_CHAT_KEY = "agent_chat"
_TICKET_CACHE_KEY = "agent_ticket_cache"

# (button label, prompt sent to the agent)
_EXAMPLE_CHAT_PROMPTS: tuple[tuple[str, str], ...] = (
    (
        "Which ticket first?",
        "Which open or pending ticket should we handle first, and why?",
    ),
    (
        "Similar billing issues",
        "Search for similar resolved tickets related to billing portal or invoice errors.",
    ),
    (
        "Summarize the queue",
        "Summarize all open and pending tickets in the queue by customer impact and urgency.",
    ),
    (
        "Highest-impact next steps",
        "What are the recommended next steps for the highest-impact open ticket?",
    ),
)


def _ticket_lookup_base() -> dict[str, SupportTicket]:
    """Queue plus any tickets resolved from prior chat replies."""
    lookup: dict[str, SupportTicket] = dict(
        st.session_state.get(_TICKET_CACHE_KEY, {})
    )
    for ticket in st.session_state.get(_QUEUE_KEY, []):
        lookup[ticket.id] = ticket
    return lookup


async def _resolve_tickets_mentioned_in_text(
    content: str, *, list_ready: bool
) -> dict[str, SupportTicket]:
    lookup = _ticket_lookup_base()
    for tid in dict.fromkeys(TICKET_ID_PATTERN.findall(content)):
        if tid in lookup or not list_ready:
            continue
        repo = TicketRepository()
        for ticket in await repo.query_jsonpath_tickets(f"$.id:{tid}"):
            if ticket.id == tid:
                lookup[tid] = ticket
                break
    st.session_state[_TICKET_CACHE_KEY] = lookup
    return lookup


def _submit_chat_turn(
    prompt: str, queue_snapshot: list[SupportTicket] | None
) -> None:
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


render_page_brand()

st.title("Customer Support Agent")
st.caption(
    "Ask questions about your customer support tickets (queue, priorities, similar resolved "
    "cases) or **Load queue** and **Triage all** to run structured triage on open and pending tickets."
)

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

    queue_snapshot: list[SupportTicket] = st.session_state[_QUEUE_KEY]

    for i, msg in enumerate(st.session_state[_CHAT_KEY]):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                tickets_by_id = asyncio.run(
                    _resolve_tickets_mentioned_in_text(
                        msg["content"], list_ready=list_ready
                    )
                )
                render_chat_message_with_ticket_links(
                    msg["content"],
                    tickets_by_id,
                    message_index=i,
                )
            else:
                st.markdown(msg["content"])

    st.caption("Example questions")
    ex_cols = st.columns(2)
    for idx, (label, example_prompt) in enumerate(_EXAMPLE_CHAT_PROMPTS):
        with ex_cols[idx % 2]:
            if st.button(
                label,
                key=f"chat_example:{idx}",
                disabled=not triage_ready,
                use_container_width=True,
            ):
                _submit_chat_turn(example_prompt, queue_snapshot)

    if prompt := st.chat_input(
        "Ask about your support tickets…",
        disabled=not triage_ready,
    ):
        _submit_chat_turn(prompt, queue_snapshot)

with triage_col:
    toolbar = st.columns([2, 2])
    load_queue = toolbar[0].button("Load queue")

    if load_queue and list_ready:
        try:
            with st.spinner("Loading open and pending tickets…"):
                st.session_state[_QUEUE_KEY] = asyncio.run(
                    TicketListService().fetch_open_and_pending()
                )
        except Exception:
            st.error(traceback.format_exc())
        else:
            n = len(st.session_state[_QUEUE_KEY])
            st.success(f"Queue loaded: **{n}** ticket(s) (open + pending).")

    queue_loaded = len(st.session_state[_QUEUE_KEY]) > 0
    triage_all = toolbar[1].button(
        "Triage all",
        disabled=not triage_ready or not queue_loaded,
        help="Run structured triage on every ticket in the loaded queue.",
    )

    queue: list[SupportTicket] = st.session_state[_QUEUE_KEY]
    results: dict[str, TriageAssessment] = st.session_state[_RESULTS_KEY]

    if triage_all and triage_ready and queue:
        try:
            progress = st.progress(0.0, text="Running triage agent…")

            async def _triage_all() -> dict[str, TriageAssessment]:
                svc = TriageService()
                batch: dict[str, TriageAssessment] = {}
                total = len(queue)
                for i, ticket in enumerate(queue, start=1):
                    progress.progress(
                        i / total, text=f"Triage {i}/{total}: {ticket.id}"
                    )
                    batch[ticket.id] = await svc.run(ticket)
                return batch

            batch = asyncio.run(_triage_all())
            st.session_state[_RESULTS_KEY] = batch
            results = batch
            progress.empty()
            st.success(f"Triage complete for **{len(batch)}** ticket(s).")
        except Exception:
            st.error(traceback.format_exc())

    if queue:
        st.subheader("Queue")
        st.caption(f"{len(queue)} ticket(s) (open or pending).")
        for ticket in queue:
            render_ticket_subject_button(
                ticket, key=f"queue_view:{ticket.id}", left_align=True
            )
            st.caption(f"`{ticket.id}` · **{ticket.status}** · {ticket.productArea}")
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
