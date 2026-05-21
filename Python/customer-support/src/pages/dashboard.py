"""Dashboard: paginated tickets from Railengine storage list."""

from __future__ import annotations

import asyncio
import traceback

import streamlit as st

from customer_support.services.ticket_list_service import TicketListService
from customer_support.streamlit_common import env_ok, render_env_metrics


st.title("Dashboard")
st.caption("Tickets loaded via `Railengine.list_storage_documents` (paginated).")

render_env_metrics()

status = env_ok()
list_ready = status["ENGINE_PAT"] and status["ENGINE_ID"]

if not list_ready:
    st.warning(
        "Set **ENGINE_PAT** and **ENGINE_ID** so the Dashboard can call `list_storage_documents`."
    )

col_a, col_b, col_c = st.columns([2, 2, 4])
page_number = int(col_a.number_input("Page", min_value=1, max_value=9999, value=1, step=1))
page_size = int(col_b.selectbox("Rows per page", options=[25, 50, 75, 100], index=1))

refresh = col_c.button("Load / refresh")

if refresh and list_ready:
    svc = TicketListService()
    try:
        with st.spinner("Loading storage page…"):
            page = asyncio.run(svc.fetch_page(page_number=page_number, page_size=page_size))
    except Exception:
        st.error(traceback.format_exc())
    else:
        st.caption(
            f"Page **{page.page_number}** of **{page.total_pages}** • total documents: **{page.total_count}**"
        )
        rows = [
            {
                "id": t.id,
                "subject": t.subject[:120] + ("…" if len(t.subject) > 120 else ""),
                "status": t.status,
                "tags": ", ".join(t.tags),
                "productArea": t.productArea,
                "createdAt": t.createdAt,
            }
            for t in page.items
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)
