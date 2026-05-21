# Customer Support Triage Agent

Enterprise-style demo: **ingest** support tickets into [Railengine](https://railengine.ai/), **search** similar resolved cases (index + vector store), and **triage** a new ticket with a [Railtracks](https://github.com/RailtownAI/railtracks) agent that returns structured JSON (priority, summary, draft reply).

## Prerequisites

- Python **3.10+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip + venv
- A Railengine project with a new engine whose schema matches the sample document in [`engine-schema.json`](engine-schema.json) (copy-paste into the engine schema editor when creating the engine).
- Enable **index** and **vector (VectorStore1)** on fields you want to search (e.g. `subject`, `body`, `tags`) in the Railengine console so `search_index` and `search_vector_store` return useful hits.
- Optional: configure **PII masking** on the engine so emails, phone numbers, and `sk-…` style secrets in `body` / `customerEmail` are masked after ingest — compare raw fixtures vs. stored documents to show compliance-friendly data.

## Setup

1. Copy environment template and add credentials from the Railengine dashboard:

   ```bash
   cd Python/customer-support
   cp .env.example .env
   ```

   - `ENGINE_TOKEN` — for ingestion (`rail-engine-ingest`)
   - `ENGINE_ID` + `ENGINE_PAT` — for retrieval/search (`rail-engine`)
   - `OPENAI_API_KEY` — for the Railtracks OpenAI model in `agent.py`

   **Note:** The ingest CLI does not import Railtracks (which wires `load_dotenv` on import), so this project calls `customer_support._env.ensure_dotenv_loaded()` at startup. That loads `Python/customer-support/.env` beside the package, then the current working directory, so `ENGINE_TOKEN` is available when you run `support-ingest`.

2. Install dependencies:

   ```bash
   uv sync
   ```

   Or: `pip install -e .`

## Seed tickets (fixtures)

Ingest historical **resolved** tickets first, then open tickets (order only matters for your mental model — the agent searches by similarity):

```bash
uv run support-ingest fixtures/tickets/resolved_*.json fixtures/tickets/ticket_001.json fixtures/tickets/ticket_002.json
```

Or:

```bash
uv run python -m customer_support.ingest fixtures/tickets/*.json
```

## Run triage on one ticket

```bash
uv run python -m customer_support.triage --ticket fixtures/tickets/ticket_001.json
```

The agent calls Railengine-backed tools (`search_similar_tickets`, `list_recent_tickets`, `get_ticket_by_id`), then emits a **`TriageAssessment`** (priority, category, internal summary, draft reply, similar ticket ids).

## Streamlit UI

Local demo browser:

```bash
cd Python/customer-support
uv sync
uv run streamlit run src/customer_support/streamlit_app.py
```

- Metrics show whether **`ENGINE_TOKEN`**, **`ENGINE_PAT`**, **`ENGINE_ID`**, and **`OPENAI_API_KEY`** are set (values are never shown).
- Sidebar: pick a **`fixtures/tickets/*.json`** file and click **Load into editor**.
- **Ingest to Railengine** and **Run triage** use the same helpers as the CLIs (`ingest_ticket`, `triage_ticket`).

**Do not expose this Streamlit server** on the public internet without authentication; it inherits the usual risks of forwarding API credentials through a prototype web app.

## Optional: webhook receiver

To exercise **activate** (webhook publishing) locally:

```bash
uv run python -m customer_support.webhook_receiver --port 8765
```

Configure the engine to POST to `http://<host>:8765/webhook`. Each event is parsed and printed as JSON (ticket id, subject, status).

## Security note

Treat this sample like other examples in this repo: **do not** expose `ENGINE_TOKEN`, `ENGINE_PAT`, or `OPENAI_API_KEY` on a public host without authentication and rate limits. Treat the Streamlit UI the same way as the CLI: keep it **local** or behind a VPN and access control.

## Layout

| Path | Purpose |
|------|---------|
| `engine-schema.json` | Sample document for engine schema setup |
| `fixtures/tickets/` | JSON tickets with **synthetic** PII and a fake API key for masking demos |
| `src/customer_support/models.py` | `SupportTicket`, `TriageAssessment` |
| `src/customer_support/tools.py` | Railtracks `@function_node` tools using `rail-engine` |
| `src/customer_support/agent.py` | Railtracks agent + structured output |
| `src/customer_support/triage.py` | CLI entrypoint |
| `src/customer_support/triage_runner.py` | Shared async `triage_ticket()` for CLI and UI |
| `src/customer_support/ingest.py` | CLI + `ingest_ticket` helper |
| `src/customer_support/streamlit_app.py` | Streamlit demo UI (ingest + triage) |
| `src/customer_support/webhook_receiver.py` | Optional stdlib HTTP webhook |

## Talk track (1 sentence)

> “Tickets land in Railengine with masking and indexing; the Railtracks agent uses your engine as the **system of record** for similar cases and returns auditable structured triage.”
