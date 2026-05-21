"""Railtracks tool nodes backed by rail-engine retrieval."""

from __future__ import annotations

import json
from typing import Any, Literal

import railtracks as rt

from customer_support.models import SupportTicket
from customer_support.rail_payload import ticket_from_row
from customer_support.runtime import get_railengine_client


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


async def _collect_index_hits(query: str, limit: int) -> list[SupportTicket]:
    """Index search returns ``IndexingSearchResult`` (rail-engine ``await``, not ``async for``)."""
    client = get_railengine_client()
    out: list[SupportTicket] = []
    result = await client.search_index(query={"search": query}, raw=True)
    for row in result.items:
        t = ticket_from_row(row)
        if t:
            out.append(t)
        if len(out) >= limit:
            break
    return out


async def _collect_vector_hits(query: str, limit: int) -> list[SupportTicket]:
    """Vector search returns ``list`` (rail-engine ``await``, not ``async for``)."""
    client = get_railengine_client()
    items = await client.search_vector_store(
        vector_store="VectorStore1",
        query=query,
        top=limit,
    )
    out: list[SupportTicket] = []
    for row in items:
        t = ticket_from_row(row)
        if t:
            out.append(t)
        if len(out) >= limit:
            break
    return out


async def _iter_raw_storage_pages(*, page_size: int, max_docs: int):
    """Walk storage pages until max_docs yielded or pages exhausted."""
    client = get_railengine_client()
    scanned = 0
    pn = 1
    while scanned < max_docs:
        page = await client.list_storage_documents(
            page_number=pn,
            page_size=page_size,
            raw=True,
        )
        for row in page.items:
            yield row
            scanned += 1
            if scanned >= max_docs:
                return
        if page.total_pages < 1 or pn >= page.total_pages:
            return
        pn += 1


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

    if mode in ("index", "both"):
        for t in await _collect_index_hits(query, limit):
            merged[t.id] = t
    if mode in ("vector", "both"):
        for t in await _collect_vector_hits(query, limit):
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
    client = get_railengine_client()
    want = status.strip().lower()
    if want not in ("open", "pending", "resolved"):
        return json.dumps(
            {"error": "status must be open, pending, or resolved"},
            indent=2,
        )

    cap = max(1, min(int(limit), 50))
    collected: list[SupportTicket] = []

    page = await client.query_storage_by_jsonpath(json_path_query=f"$.status:{want}")
    for row in page.items:
        t = ticket_from_row(row)
        if t:
            collected.append(t)
        if len(collected) >= cap:
            break

    if len(collected) < cap:
        max_scan = 400
        seen_ids = {t.id for t in collected}
        async for row in _iter_raw_storage_pages(page_size=100, max_docs=max_scan):
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
    tid = ticket_id.strip()
    if not tid:
        return json.dumps({"error": "ticket_id required"}, indent=2)

    client = get_railengine_client()

    page = await client.query_storage_by_jsonpath(json_path_query=f"$.id:{tid}")
    for row in page.items:
        t = ticket_from_row(row)
        if t and t.id == tid:
            return json.dumps(_ticket_to_brief(t), ensure_ascii=False, indent=2)

    async for row in _iter_raw_storage_pages(page_size=100, max_docs=500):
        t = ticket_from_row(row)
        if t and t.id == tid:
            return json.dumps(_ticket_to_brief(t), ensure_ascii=False, indent=2)

    return json.dumps({"error": f"ticket not found: {tid}"}, indent=2)
