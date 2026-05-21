"""Railtracks triage flow orchestration."""

from __future__ import annotations

import json

import railtracks as rt
from railtracks.built_nodes.concrete.response import StructuredResponse

from customer_support.agents.triage_agent import build_triage_agent, build_triage_chat_agent
from customer_support.models import SupportTicket, TriageAssessment


def _flow_reply_text(result: object) -> str:
    if isinstance(result, StructuredResponse):
        structured = result.structured
        if hasattr(structured, "model_dump_json"):
            return structured.model_dump_json(indent=2)
        return str(structured)
    if hasattr(result, "content"):
        return str(result.content)
    return str(result)


class TriageService:
    """Run the structured triage agent (tools use TicketRepository internally)."""

    async def run(self, ticket: SupportTicket) -> TriageAssessment:
        agent_cls = build_triage_agent()
        flow = rt.Flow(name="CustomerSupportTriage", entry_point=agent_cls)

        prompt = f"""Triage this ticket:

```json
{json.dumps(ticket.model_dump(), indent=2, ensure_ascii=False)}
```

1) Call search_similar_tickets with a query built from subject, body, and productArea.
2) Optionally call list_recent_tickets(status="resolved") for extra historical context.
3) Return a TriageAssessment with priority, category, internal_summary, draft_reply_to_customer, similar_ticket_ids, and reasoning.
"""
        result = await flow.ainvoke(prompt)
        if isinstance(result, StructuredResponse):
            structured = result.structured
            if isinstance(structured, TriageAssessment):
                return structured
            return TriageAssessment.model_validate(structured)
        if isinstance(result, TriageAssessment):
            return result
        if hasattr(result, "model_dump"):
            return TriageAssessment.model_validate(result.model_dump())
        raise TypeError(f"Unexpected agent result type: {type(result)}")

    async def run_batch(self, tickets: list[SupportTicket]) -> dict[str, TriageAssessment]:
        """Triage each ticket sequentially (one agent run per ticket)."""
        results: dict[str, TriageAssessment] = {}
        for ticket in tickets:
            results[ticket.id] = await self.run(ticket)
        return results

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        queue: list[SupportTicket] | None = None,
    ) -> str:
        """Free-form chat with the triage agent (same tools, conversational reply)."""
        agent_cls = build_triage_chat_agent()
        flow = rt.Flow(name="CustomerSupportTriageChat", entry_point=agent_cls)

        parts: list[str] = []
        if queue:
            lines = [f"- {t.id} ({t.status}): {t.subject}" for t in queue[:30]]
            parts.append("Open/pending queue in Railengine:\n" + "\n".join(lines))

        transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        parts.append(f"Conversation:\n{transcript}")

        prompt = "\n\n".join(parts) + "\n\nRespond to the latest USER message."
        result = await flow.ainvoke(prompt)
        return _flow_reply_text(result)
