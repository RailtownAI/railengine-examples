"""Streamlit multipage entry: Dashboard, Search, Ingest, Agent."""

from __future__ import annotations

import streamlit as st

from customer_support.config.env import ensure_dotenv_loaded
from customer_support.streamlit_common import use_full_width_layout


def main() -> None:
    ensure_dotenv_loaded()
    st.set_page_config(page_title="Support Triage", layout="wide")
    use_full_width_layout()
    pg = st.navigation(
        [
            st.Page("pages/dashboard.py", title="Dashboard", icon="🗂️", default=True),
            st.Page("pages/search_page.py", title="Search", icon="🔍"),
            st.Page("pages/ingest_page.py", title="Ingest", icon="📥"),
            st.Page("pages/agent_page.py", title="Agent", icon="🤖"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
