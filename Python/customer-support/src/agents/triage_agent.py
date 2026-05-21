"""Railtracks triage agent definition."""

from __future__ import annotations

import os

import railtracks as rt

from customer_support.agents.tools import (
    get_ticket_by_id,
    list_recent_tickets,
    search_similar_tickets,
)
from customer_support.models import TriageAssessment


def build_triage_agent():
    """Create agent with structured JSON output and Railengine-backed tools."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or export it before running triage."
        )

    llm = rt.llm.OpenAILLM("gpt-5.4")

    system = """You are an enterprise support triage lead. You receive a single support ticket (JSON).

Rules:
- Use the search tools to find similar RESOLVED tickets before writing a reply.
- Never copy API keys, tokens, or passwords into the draft_reply — refer to them only as "the credential mentioned in the ticket" if needed.
- Prioritize customer impact and whether the issue blocks billing, security, or wide outages.
- Populate similar_ticket_ids with ids you actually saw from tool results (may be empty if none).
- Keep internal_summary factual and concise.
"""

    return rt.agent_node(
        "Support Triage Agent",
        tool_nodes=(
            search_similar_tickets,
            list_recent_tickets,
            get_ticket_by_id,
        ),
        llm=llm,
        system_message=system,
        output_schema=TriageAssessment,
    )


def build_triage_chat_agent():
    """Conversational triage lead with the same Railengine tools (no structured output)."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or export it before running triage."
        )

    llm = rt.llm.OpenAILLM("gpt-5.4")

    system = """You are an enterprise support triage lead chatting with a human support manager.

You help prioritize open and pending tickets, explain customer impact, and suggest next steps.
Use search_similar_tickets, list_recent_tickets, and get_ticket_by_id when you need historical context from Railengine.
Never paste API keys, tokens, or passwords — refer to them only as credentials mentioned in a ticket.
Be concise and actionable. When comparing tickets, state priority rationale clearly (P1–P4 style).
"""

    return rt.agent_node(
        "Support Triage Chat Agent",
        tool_nodes=(
            search_similar_tickets,
            list_recent_tickets,
            get_ticket_by_id,
        ),
        llm=llm,
        system_message=system,
    )
