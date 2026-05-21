"""Railtracks tool nodes backed by TicketRepository (no global SDK client)."""

from __future__ import annotations

import json
from typing import Any, Literal

import railtracks as rt

from customer_support.models import SupportTicket
from customer_support.repositories import TicketRepository
from customer_support.repositories.mappers import ticket_from_row


def _ticket_to_brief(t: SupportTicket) -> dict[str, Any]:
    return {
        "id": t.id,
        "subject": t.subject,
        "status": t.status,
        "tags": t.tags,
        "productArea": t.productArea,
        "createdAt": t.createdAt,
        "body_excerpt": (t.body[:280] + "…") if len(t.body) > 280 else t.body,
    }


@rt.function_node
async def search_similar_tickets(
    query: str,
    mode: Literal["vector", "index", "both"] = "both",
    limit: int = 6,
) -> str:
    """
    Search historical tickets in Railengine using keyword index and/or semantic vector search.

    Args:
        query: Natural language or keywords describing the issue (subject + symptoms).
        mode: Use embedding search (vector), keyword index (index), or run both and merge.
        limit: Max tickets to return per search mode (capped for latency).
    """
    limit = max(1, min(int(limit), 25))
    merged: dict[str, SupportTicket] = {}
    repo = TicketRepository()

    if mode in ("index", "both"):
        for t in await repo.search_index_hits(query, limit):
            merged[t.id] = t
    if mode in ("vector", "both"):
        for t in await repo.search_vector_hits(query, limit):
            merged[t.id] = t

    briefs = [_ticket_to_brief(t) for t in merged.values()]
    return json.dumps(briefs, ensure_ascii=False, indent=2)


@rt.function_node
async def list_recent_tickets(status: str = "resolved", limit: int = 15) -> str:
    """
    List recent tickets from hot storage. Filter client-side by status.

    Args:
        status: open | pending | resolved — only tickets matching this status are returned.
        limit: Max rows to return (JSONPath query when supported; otherwise capped scan).
    """
    repo = TicketRepository()
    want = status.strip().lower()
    if want not in ("open", "pending", "resolved"):
        return json.dumps(
            {"error": "status must be open, pending, or resolved"},
            indent=2,
        )

    cap = max(1, min(int(limit), 50))
    collected: list[SupportTicket] = []

    for t in await repo.query_jsonpath_tickets(f"$.status:{want}"):
        collected.append(t)
        if len(collected) >= cap:
            break

    if len(collected) < cap:
        max_scan = 400
        seen_ids = {t.id for t in collected}
        async for row in repo.iter_raw_storage_pages(page_size=100, max_docs=max_scan):
            t = ticket_from_row(row)
            if not t or t.status != want:
                continue
            if t.id in seen_ids:
                continue
            seen_ids.add(t.id)
            collected.append(t)
            if len(collected) >= cap:
                break

    return json.dumps(
        [_ticket_to_brief(t) for t in collected],
        ensure_ascii=False,
        indent=2,
    )


@rt.function_node
async def get_ticket_by_id(ticket_id: str) -> str:
    """
    Fetch a ticket by its business id (the `id` field inside the ingested JSON document).

    Uses JSONPath storage query when available; falls back to a capped scan of recent pages.
    """
    repo = TicketRepository()
    tid = ticket_id.strip()
    if not tid:
        return json.dumps({"error": "ticket_id required"}, indent=2)

    for t in await repo.query_jsonpath_tickets(f"$.id:{tid}"):
        if t.id == tid:
            return json.dumps(_ticket_to_brief(t), ensure_ascii=False, indent=2)

    async for row in repo.iter_raw_storage_pages(page_size=100, max_docs=500):
        t_row = ticket_from_row(row)
        if t_row and t_row.id == tid:
            return json.dumps(_ticket_to_brief(t_row), ensure_ascii=False, indent=2)

    return json.dumps({"error": f"ticket not found: {tid}"}, indent=2)
