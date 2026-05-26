# Customer Support Triage

Demo stack: ingest support tickets into [Railengine](https://railengine.ai/), search resolved history (keyword index + `VectorStore1`), and triage a case with [Railtracks](https://github.com/RailtownAI/railtracks) structured output (priority, category, summaries, draft reply).

## Before you start

- A [Railengine](https://railengine.ai/) account plus a **new engine** configured with the sample schema in [`engine-schema.json`](engine-schema.json).
- Select that schema into your engine creation modal so documents match **`SupportTicket`**.
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
2. (Optional breadth) On **Ingest**, use sidebar **Seed all fixtures** to ingest every `fixtures/tickets/*.json`.
3. On **Ingest**, click **Run triage** on a single ticket, or open **Agent** → **Load queue** → **Triage all** for open and pending tickets.
4. Switch to **Dashboard**, click **Refresh board**, and browse the Kanban. Click a **card subject** to open ticket details in a dialog; change status from the card **dropdown** (**requires `ENGINE_TOKEN`** alongside list credentials).
5. Open **Search**, enter keywords (e.g. `billing invoice`), and press **Enter** or **🔍 Search** to query the keyword index. Select a row (or **📋 Details**) to open the ticket dialog.

## Debug and visualize the triage agent (optional)

After you run triage once (**Ingest** or **Agent**), inspect agent runs in the Railtracks UI:

```bash
cd Python/customer-support
railtracks update
railtracks viz
```

(`railtracks[visual]` is included in project dependencies; run `uv sync` if you have not already.)

Opens the local visualization app so you can debug tool calls, prompts, and structured output from the support triage flow.

## Environment variables

| Variable | Used for | Required when |
|----------|-----------|---------------|
| `ENGINE_TOKEN` | Ingest SDK | **Ingest** page · **Kanban status** dropdown |
| `ENGINE_PAT` | Retrieval / list / search | **Dashboard**, **Search**, triage tools |
| `ENGINE_ID` | Engine routing | **Dashboard**, **Search**, triage tools |
| `OPENAI_API_KEY` | Railtracks LLM | **Run triage** |

A local `.env` next to [`pyproject.toml`](pyproject.toml) is loaded automatically for Streamlit and the webhook receiver.

<details>
<summary>Optional: PII masking</summary>

If your engine masks sensitive fields after ingest, compare raw fixtures to stored docs in the dashboard to illustrate compliance-aware storage.</details>

## Project layout

Code is organized in layers so UI, business logic, and Railengine I/O stay separate. Imports use the **`customer_support`** package (`pyproject.toml` maps `src/` to that name).

```text
pages / controllers  →  services  →  repositories  →  rail-engine / rail-engine-ingest
                              ↓
                           models
agents (tools)  →  services or repositories
```

| Path | Role | Examples |
|------|------|----------|
| [`src/models/`](src/models/) | Pydantic domain types and constants | `SupportTicket`, `TriageAssessment`, `TicketPage` |
| [`src/repositories/`](src/repositories/) | SDK calls only (`Railengine`, `RailengineIngest` with `model=SupportTicket`) | `TicketRepository` — list, search, ingest, JSONPath |
| [`src/services/`](src/services/) | Use-case orchestration; pages call these, not the SDK | `IngestService`, `TicketListService`, `SearchService`, `TriageService` |
| [`src/agents/`](src/agents/) | Railtracks structured agent, chat agent, and tool nodes | `triage_agent.py`, `tools.py` (`search_similar_tickets`, …) |
| [`src/pages/`](src/pages/) | Streamlit screens (thin UI + session state) | `dashboard.py`, `search_page.py`, `ingest_page.py`, `agent_page.py` |
| [`src/controllers/`](src/controllers/) | Optional non-UI entry points | [`webhook.py`](src/controllers/webhook.py) — local publishing smoke test |
| [`src/config/`](src/config/) | Environment bootstrap | `ensure_dotenv_loaded()` loads `.env` next to `pyproject.toml` |
| [`src/streamlit_app.py`](src/streamlit_app.py) | App entry: `st.navigation` for Dashboard / Search / Ingest / Agent | `uv run streamlit run src/streamlit_app.py` |
| [`src/streamlit_common.py`](src/streamlit_common.py) | Shared UI (brand, toolbar, Kanban cards, ticket dialog, pipeline diagram) | Used across pages |

**Repository root (besides `src/`)**

- [`engine-schema.json`](engine-schema.json) — paste into the Railengine console when creating the engine
- [`fixtures/tickets/`](fixtures/tickets/) — sample `SupportTicket` JSON for ingest demos
- [`assets/`](assets/) — Streamlit branding (e.g. logo)
- [`.env.example`](.env.example) — required env var template

## Local only

**Do not** expose the Streamlit app on the public internet with live credentials unless you add authentication and hardening yourself.

## Optional: webhook receiver

Activation / publishing smoke test:

```bash
uv run python -m customer_support.controllers.webhook --port 8765
```

POST to `http://127.0.0.1:8765/webhook` (tunnel with ngrok if you need a public URL).
