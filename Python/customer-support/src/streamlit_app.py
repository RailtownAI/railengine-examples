"""Streamlit multipage entry: Dashboard, Ingest, Triage Agent."""

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
            st.Page("pages/ingest_page.py", title="Ingest", icon="📥"),
            st.Page("pages/triage_agent_page.py", title="Triage Agent", icon="🤖"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
