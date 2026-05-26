"""Streamlit page: Railengine index search."""

from __future__ import annotations

import asyncio
import traceback
from typing import Any

import streamlit as st

from customer_support.models import SupportTicket
from customer_support.services.search_service import SearchService
from customer_support.streamlit_common import (
    env_ok,
    render_app_toolbar,
    render_page_brand,
    show_ticket_details_dialog,
)

_SEARCH_RESULTS_KEY = "search_results"
_SEARCH_DF_KEY = "search_results_df"
_DEFAULT_LIMIT = 50


def _trunc_subject(subject: str, *, max_len: int = 140) -> str:
    return subject[:max_len] + ("…" if len(subject) > max_len else "")


def _tickets_to_table_rows(tickets: list[SupportTicket]) -> list[dict[str, str]]:
    return [
        {
            "id": t.id,
            "subject": _trunc_subject(t.subject),
            "status": t.status,
            "tags": ", ".join(t.tags),
            "productArea": t.productArea,
            "createdAt": t.createdAt,
        }
        for t in tickets
    ]


def _selected_row_index(df_key: str) -> int | None:
    """Row index from ``st.dataframe`` selection state (dict or widget state object)."""
    state: Any = st.session_state.get(df_key)
    if state is None:
        return None
    selection = (
        state.get("selection")
        if isinstance(state, dict)
        else getattr(state, "selection", None)
    )
    if selection is None:
        return None
    rows = (
        selection.get("rows")
        if isinstance(selection, dict)
        else getattr(selection, "rows", None)
    )
    if not rows:
        return None
    return int(rows[0])


def _open_details_for_selected_row() -> None:
    """``on_select`` callback: open ticket dialog for the newly selected row."""
    idx = _selected_row_index(_SEARCH_DF_KEY)
    if idx is None:
        return
    tickets: list[SupportTicket] = st.session_state.get(_SEARCH_RESULTS_KEY, [])
    if 0 <= idx < len(tickets):
        show_ticket_details_dialog(tickets[idx])


render_page_brand()
render_app_toolbar()

st.title("Search")
st.caption(
    "Find tickets in Railengine using the **keyword index** (`search_index`). "
    "Use subject keywords, product area, or phrases from ticket bodies."
)

env = env_ok()
search_ready = env["ENGINE_PAT"] and env["ENGINE_ID"]

if not search_ready:
    st.warning("Set **ENGINE_PAT** and **ENGINE_ID** to search Railengine.")

if _SEARCH_RESULTS_KEY not in st.session_state:
    st.session_state[_SEARCH_RESULTS_KEY] = []

with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        "Search query",
        placeholder="e.g. billing portal invoice 500",
        disabled=not search_ready,
    )
    limit = st.slider(
        "Max results",
        min_value=5,
        max_value=100,
        value=_DEFAULT_LIMIT,
        step=5,
        disabled=not search_ready,
    )
    run_search = st.form_submit_button(
        "🔍 Search",
        disabled=not search_ready,
        type="primary",
    )

if run_search and query.strip():
    try:
        with st.spinner("Searching Railengine index…"):
            st.session_state[_SEARCH_RESULTS_KEY] = asyncio.run(
                SearchService().search_index(query.strip(), limit=limit)
            )
        if _SEARCH_DF_KEY in st.session_state:
            del st.session_state[_SEARCH_DF_KEY]
    except Exception:
        st.error(traceback.format_exc())
    else:
        n = len(st.session_state[_SEARCH_RESULTS_KEY])
        st.success(f"Found **{n}** ticket(s) for `{query.strip()}`.")

results: list[SupportTicket] = st.session_state[_SEARCH_RESULTS_KEY]

if results:
    st.subheader("Results")
    st.caption(
        "Select a row in the table (checkbox on the left) to open **Ticket details**. "
        "You can also use **📋 Details** after selecting a row."
    )
    st.dataframe(
        _tickets_to_table_rows(results),
        hide_index=True,
        width="stretch",
        on_select=_open_details_for_selected_row,
        selection_mode="single-row",
        key=_SEARCH_DF_KEY,
    )
    selected_idx = _selected_row_index(_SEARCH_DF_KEY)
    if st.button(
        "📋 Details",
        disabled=selected_idx is None,
        type="secondary",
    ):
        if selected_idx is not None and 0 <= selected_idx < len(results):
            show_ticket_details_dialog(results[selected_idx])
elif search_ready and not run_search:
    st.info(
        "Enter a query and press **Enter** or click **🔍 Search** "
        "to query the Railengine index."
    )
