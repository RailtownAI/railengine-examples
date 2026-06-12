# Daily Insight (Railtracks)

A small Python service that mirrors the **Daily Insight** feature from [`CSharp/Examples/RailenginePoweredStatusPage`](../../CSharp/Examples/RailenginePoweredStatusPage/): given a Railengine of metric records, ask an LLM to produce a one-line-per-metric plain-text summary of recent values.

Where the C# version drives the LLM through an Anthropic MCP server attached as a tool source, this version drives it through [Railtracks](https://github.com/RailtownAI/railtracks) with a single `@rt.function_node` tool that calls the [Railengine Python SDK](https://pypi.org/project/rail-engine/) directly.

## Before you start

- A [Railengine](https://railengine.ai/) engine populated with `MetricRecord`-shaped documents (`metric`, `timestamp`, `value` — see [`MetricRecord`](src/models/metric.py)). The C# status page example produces records in exactly this shape.
- An Anthropic API key with access to `claude-haiku-4-5-20251001` (or another model you set via `LLM_MODEL`).

## Quick start

```bash
cd Python/daily-insight
cp .env.example .env       # fill ENGINE_ID, ENGINE_PAT, LLM_API_KEY
uv sync
uv run uvicorn daily_insight.controllers.api:app --reload --port 8000
```

Then:

```bash
# Liveness
curl http://127.0.0.1:8000/health

# Generate a fresh insight
curl -X POST http://127.0.0.1:8000/insight

# Generate fresh insight(s) and evaluate them
curl -X POST http://127.0.0.1:8000/evals/run -H 'Content-Type: application/json' -d '{"sample_size": 1}'
```

`POST /insight` runs the Railtracks agent against your engine and returns:

```json
{
  "text": "latency-p95: Latest reading 87.3 ms, trending down over the last 50 samples.\nerror-rate: Holding flat near 2.4 errors/min.\n...",
  "generated_at": "2026-06-12T18:42:11.123456+00:00",
  "metric_count": 4,
  "error": null
}
```

Expect each call to take a few seconds — the agent makes one Anthropic call plus one Railengine GET. The exact latency depends on the model.

## Evaluation

`POST /evals/run` runs Railtracks evaluators against agent sessions and returns the scores. Two modes:

| Mode | Trigger | Cost | What it evaluates |
|---|---|---|---|
| **Fresh** (default) | body omits `agent_run_id` | ≈ `sample_size · 3` LLM calls | Generates `sample_size` brand-new `/insight` runs (default 1, capped at 5) and scores them. Self-contained smoke test. |
| **Historical** | body sets `agent_run_id` | ≈ 2 LLM calls (judge only) | Fetches the named past run from Conductr via [`railtownai.get_agent_runs`](https://pypi.org/project/railtownai/) and scores that single session. Replays a real production interaction without re-spending generation cost. |

```bash
# Fresh (default)
curl -X POST .../evals/run -H 'Content-Type: application/json' -d '{"sample_size": 1}'

# Historical
curl -X POST .../evals/run -H 'Content-Type: application/json' \
  -d '{"agent_run_id": "0466964a-1234-5678-9abc-def012345678"}'
```

When `RAILTOWN_API_KEY` is set, each `EvaluationResult` also uploads to Conductr via `railtownai.upload_agent_evaluation`.

Three evaluators run per call (see [`agents/evaluations.py`](src/agents/evaluations.py)):

- **`ToolUseEvaluator`** (free, local) — checks the agent's tool call pattern. The system prompt says "use AT MOST 1 tool call to `get_recent_metrics`"; this catches regressions where the model skips it or over-calls.
- **`LLMInferenceEvaluator`** (free, local) — checks the LLM call pattern (latency, tokens, errors).
- **`JudgeEvaluator`** with two custom metrics:
  - **`FormatCompliance`** (Compliant / MinorDeviation / MajorDeviation) — does the response follow the strict one-line-per-metric format that the C# card expects to render unchanged?
  - **`FactualGrounding`** (FullyGrounded / PartiallyGrounded / Hallucinated) — does every value and trend in the response trace back to the tool output, or is the model inventing things?

Override the judge model via `EVAL_JUDGE_MODEL`; defaults to `LLM_MODEL` or `claude-haiku-4-5-20251001`.

**Historical-mode prerequisites.** The agent fetches sessions from Conductr's platform API, so it needs:

- `CONDUCTR_PROJECT_ID` — already present in deployed environments (the deploy tooling seeds it).
- `CONDUCTR_PROJECT_PAT` — a project-level access token generated in the Conductr UI under *project → Secret Tokens*. Not yet auto-seeded by the deploy tooling; for a deployed agent, set it once with `az keyvault secret set --vault-name <kv> --name CONDUCTR-PROJECT-PAT --value '<token>'` and roll a config-only revision to wire it onto the container.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `ENGINE_ID` | Yes | Railengine engine GUID — same one the C# status page reads from |
| `ENGINE_PAT` | Yes | Railengine PAT used for retrieval |
| `LLM_API_KEY` | Yes | Anthropic API key. Provider-neutral name so the same setting works across agents; on startup the value is copied into `ANTHROPIC_API_KEY` for the Anthropic SDK to pick up. `ANTHROPIC_API_KEY` is also accepted directly if you prefer the SDK-native name. |
| `LLM_MODEL` | No | Override the default Claude model (`claude-haiku-4-5-20251001`) |
| `RAILTOWN_API_KEY` | No | Enables Railtown observability. When set, the agent ships its logs (and any unhandled-exception tracebacks from the global handler) to Railtown via the [`railtownai`](https://pypi.org/project/railtownai/) logging handler. Unset → no observability, agent runs normally. |
| `RAILTOWN_API_URL` | No | Override the Railengine API host (defaults to production) |

Variables are read from `.env` next to `pyproject.toml`, then from the process environment.

## Project layout

```text
controllers (FastAPI)  →  services  →  agents (Railtracks)  →  repositories  →  rail-engine
                                                ↓
                                             models
```

| Path | Role |
|---|---|
| [`src/models/`](src/models/) | Pydantic types — `MetricRecord`, `DailyInsight` |
| [`src/repositories/`](src/repositories/) | [`MetricRepository`](src/repositories/metric_repository.py) — wraps `Railengine.list_storage_documents` |
| [`src/agents/`](src/agents/) | [`tools.py`](src/agents/tools.py) defines the `get_recent_metrics` function node; [`insight_agent.py`](src/agents/insight_agent.py) wires it to `rt.llm.AnthropicLLM` |
| [`src/services/`](src/services/) | [`InsightService`](src/services/insight_service.py) — runs the `rt.Flow` and shapes the response |
| [`src/controllers/`](src/controllers/) | [`api.py`](src/controllers/api.py) — FastAPI app with `/health` and `/insight` |
| [`src/config/`](src/config/) | `.env` loading and required-env validation |

## How this differs from the C# version

The C# [`DailyInsightService`](../../CSharp/Examples/RailenginePoweredStatusPage/Services/DailyInsightService.cs) is a `BackgroundService` that wakes once every 24 hours and posts to `/v1/messages` with the Railengine MCP server (`mcp_servers`) attached, then streams the response. The same prompt and output format are used here.

This Python version:

- Replaces the MCP attachment with a Railtracks `@rt.function_node` tool (`get_recent_metrics`) that calls the Railengine Python SDK directly. The LLM still chooses when to call it, but the schema and execution are local.
- Replaces the 24h `BackgroundService` with an on-demand HTTP endpoint. A scheduler (cron, GitHub Actions, Azure Logic Apps, etc.) can POST `/insight` daily if you want the same cadence.
- Keeps the strict plain-text output rules so the existing C# `Daily Insight` card can render the result unchanged.

## Containerization

A [`Dockerfile`](Dockerfile) is included so the service can be containerized for deployment. The image installs the package via `pyproject.toml` and runs `uvicorn daily_insight.controllers.api:app` on port 8000. Build and run locally with:

```bash
docker build -t daily-insight .
docker run --rm -p 8000:8000 --env-file .env daily-insight
```

If you put the agent behind a reverse proxy that requires bearer auth, the C# caller in [`RailenginePoweredStatusPage`](../../CSharp/Examples/RailenginePoweredStatusPage/) can attach the token via the `DailyInsight:AgentBearerToken` setting — `DailyInsightService.GenerateFromAgentAsync` adds it as `Authorization: Bearer <token>` when non-empty.

## Debug and visualize the agent (optional)

After at least one insight run:

```bash
cd Python/daily-insight
railtracks update
railtracks viz
```

(`railtracks[visual]` is in `pyproject.toml`; run `uv sync` if you have not already.) Opens the local visualization app for inspecting tool calls and prompts.

## Local only

Don't expose this service on the public internet without authentication — `/insight` triggers a paid LLM call and a Railengine read on every invocation.
