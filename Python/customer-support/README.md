# Customer Support Triage

Demo stack: ingest support tickets into [Railengine](https://railengine.ai/), search resolved history (keyword index + `VectorStore1`), and triage a case with [Railtracks](https://github.com/RailtownAI/railtracks) structured output (priority, category, summaries, draft reply).

## Before you start

- A [Railengine](https://railengine.ai/) account plus a **new engine** configured with the sample schema in [`engine-schema.json`](engine-schema.json).
- Paste that schema into your engine schema editor so documents match **`SupportTicket`**.
- Allowed ticket **`status`** values when ingesting vs. validating in-app: **`pending`**, **`open`**, **`in_progress`**, **`resolved`** — update long-lived engine/schema rules if yours differ before re-ingesting fixtures.
- Enable **Index** plus **VectorStore1** on fields such as `subject`, `body`, and `tags` in the Railengine console so search tools get useful hits beyond raw storage scans.

## Quick start

From `Python/customer-support/`:

```bash
cd Python/customer-support
cp .env.example .env   # fill ENGINE_TOKEN, ENGINE_ID, ENGINE_PAT, OPENAI_API_KEY
uv sync
uv run streamlit run src/streamlit_app.py
```

## First demo flow

1. Open **Ingest**, load **`fixtures/tickets/ticket_001.json`**, and click **Ingest to Railengine**.
2. (Optional breadth) Seed the rest:
   `uv run support-ingest fixtures/tickets/resolved_*.json fixtures/tickets/pending_001.json fixtures/tickets/ticket_002.json`
3. On **Ingest**, click **Run triage** on a single ticket, or open **Triage Agent** → **Load queue** → **Triage queue** to prioritize all **open** and **pending** tickets.
4. Switch to **Dashboard**, click **Refresh board**, and browse the Kanban. Click a **card subject** to open ticket details in a dialog; change status from the card **dropdown** (**requires `ENGINE_TOKEN`** alongside list credentials).

## CLI (optional)

```bash
uv run support-ingest fixtures/tickets/*.json
uv run support-triage --ticket fixtures/tickets/ticket_001.json
```

## Debug and visualize the triage agent (optional)

After you run triage once (Streamlit **Triage Agent** / **Ingest**, or `support-triage`), you can inspect agent runs in the Railtracks UI:

```bash
cd Python/customer-support
pip install 'railtracks[visual]'
railtracks update
railtracks viz
```

Opens the local visualization app so you can debug tool calls, prompts, and structured output from the support triage flow.

## Environment variables

| Variable | Used for | Required when |
|----------|-----------|---------------|
| `ENGINE_TOKEN` | Ingest SDK | **Ingest** page · `support-ingest` · **Kanban status** dropdown |
| `ENGINE_PAT` | Retrieval / list | **Dashboard** / triage tools |
| `ENGINE_ID` | Engine routing | **Dashboard** / triage tools |
| `OPENAI_API_KEY` | Railtracks LLM | **Run triage** |

A local `.env` next to [`pyproject.toml`](pyproject.toml) is loaded automatically for CLIs and Streamlit.

<details>
<summary>Optional: PII masking</summary>

If your engine masks sensitive fields after ingest, compare raw fixtures to stored docs in the dashboard to illustrate compliance-aware storage.</details>

## Project layout

- `src/models/` — Pydantic shapes (`customer_support.models` at import time)
- `src/repositories/` — Railengine / ingest SDK I/O
- `src/services/` — ingest, list, triage use cases
- `src/controllers/` — CLI + webhook only
- `src/agents/` — Railtracks agent + tools
- `src/pages/` — Streamlit Dashboard, Ingest, and Triage Agent
- [`src/streamlit_app.py`](src/streamlit_app.py) — navigation entry (importable as `customer_support.streamlit_app`)

## Local only

Treat Streamlit like the CLI prototypes in this repo: **do not** expose it on the public internet with live credentials unless you add authentication and hardening yourself.

## Optional: webhook receiver

Activation / publishing smoke test:

```bash
uv run python -m customer_support.controllers.webhook --port 8765
```

POST to `http://127.0.0.1:8765/webhook` (tunnel with ngrok if you need a public URL).
