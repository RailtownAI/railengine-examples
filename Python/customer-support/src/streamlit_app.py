"""Streamlit multipage entry: Dashboard + Ingest."""

from __future__ import annotations

import streamlit as st

from customer_support.config.env import ensure_dotenv_loaded


def main() -> None:
    ensure_dotenv_loaded()
    st.set_page_config(page_title="Support Triage", layout="wide")
    pg = st.navigation(
        [
            st.Page("pages/dashboard.py", title="Dashboard", default=True),
            st.Page("pages/ingest_page.py", title="Ingest"),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()
