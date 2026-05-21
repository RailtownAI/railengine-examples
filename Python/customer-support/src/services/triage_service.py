"""Railtracks triage flow orchestration."""

from __future__ import annotations

import json

import railtracks as rt
from railtracks.built_nodes.concrete.response import StructuredResponse

from customer_support.agents.triage_agent import build_triage_agent
from customer_support.models import SupportTicket, TriageAssessment


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
