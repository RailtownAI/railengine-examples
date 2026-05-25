"""Streamlit multipage entry: Dashboard, Ingest, Agent."""

from __future__ import annotations

import streamlit as st

from customer_support.config.env import ensure_dotenv_loaded
from customer_support.streamlit_common import render_config_button, use_full_width_layout


def main() -> None:
    ensure_dotenv_loaded()
    st.set_page_config(page_title="Support Triage", layout="wide")
    use_full_width_layout()
    render_config_button()
    pg = st.navigation(
        [
            st.Page("pages/dashboard.py", title="Dashboard", icon="🗂️", default=True),
            st.Page("pages/ingest_page.py", title="Ingest", icon="📥"),
            st.Page("pages/agent_page.py", title="Agent", icon="🤖"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
