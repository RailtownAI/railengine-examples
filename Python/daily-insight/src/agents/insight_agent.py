"""Railtracks insight agent definition."""

from __future__ import annotations

import os

import railtracks as rt

from daily_insight.agents.tools import get_recent_metrics


DEFAULT_MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are an automated reviewer for a status page dashboard.

Use AT MOST 1 tool call. Call `get_recent_metrics` with limit=50 to fetch the most recent metric records, then summarize. Do not make additional exploratory calls.

Output format (strict):
- One single line per metric, nothing else.
- Format: "{Metric name}: {one-sentence insight including the latest value and any notable trend}"
- Plain text only. No markdown, no headers, no bullets, no emoji, no bold.
- No preamble, no commentary about your process, no closing remarks.
- If a metric is flat, say so concisely."""


def build_insight_agent():
    """Create the Railtracks insight agent backed by AnthropicLLM."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to .env or export it before running."
        )

    model = os.environ.get("INSIGHT_MODEL", "").strip() or DEFAULT_MODEL
    llm = rt.llm.AnthropicLLM(model)

    return rt.agent_node(
        "Daily Insight Agent",
        tool_nodes=(get_recent_metrics,),
        llm=llm,
        system_message=SYSTEM_PROMPT,
    )
