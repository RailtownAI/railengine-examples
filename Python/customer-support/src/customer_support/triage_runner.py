"""Shared async triage runner for CLI and Streamlit."""

from __future__ import annotations

import json

import railtracks as rt
from railtracks.built_nodes.concrete.response import StructuredResponse
from railtown.engine import Railengine

from customer_support.agent import build_triage_agent
from customer_support.models import SupportTicket, TriageAssessment
from customer_support.runtime import set_railengine_client


async def triage_ticket(ticket: SupportTicket) -> TriageAssessment:
    """Run the Railtracks triage Flow against Railengine-backed tools."""
    async with Railengine() as engine:
        set_railengine_client(engine)
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
