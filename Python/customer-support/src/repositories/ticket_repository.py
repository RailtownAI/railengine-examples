"""Railengine ingest + retrieval I/O."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from railtown.engine import Railengine
from railtown.engine.ingest import RailengineIngest

from customer_support.models import SupportTicket, TicketPage


def _as_ticket(item: Any) -> SupportTicket | None:
    """Coerce SDK hits to ``SupportTicket`` (model instances or fallback dict parse)."""
    if isinstance(item, SupportTicket):
        return item
    if isinstance(item, dict):
        try:
            return SupportTicket.model_validate(item)
        except Exception:
            return None
    return None


def _collect_tickets(items: list[Any]) -> list[SupportTicket]:
    out: list[SupportTicket] = []
    for item in items:
        t = _as_ticket(item)
        if t is not None:
            out.append(t)
    return out


async def ingest_ticket_with_client(
    client: RailengineIngest, ticket: SupportTicket
) -> int:
    """Upsert using an existing ingest client."""
    resp = await client.upsert(ticket)
    return resp.status_code


class TicketRepository:
    """SDK-backed ticket persistence and search."""

    async def upsert(self, ticket: SupportTicket) -> int:
        async with RailengineIngest(model=SupportTicket) as client:
            return await ingest_ticket_with_client(client, ticket)

    async def ingest_paths(self, paths: list[Path]) -> list[tuple[str, int]]:
        """Batch ingest preserving a single ingest session."""
        results: list[tuple[str, int]] = []
        async with RailengineIngest(model=SupportTicket) as client:
            for path in paths:
                raw = json.loads(path.read_text(encoding="utf-8"))
                ticket = SupportTicket.model_validate(raw)
                status = await ingest_ticket_with_client(client, ticket)
                results.append((path.name, status))
        return results

    async def list_page(self, page_number: int = 1, page_size: int = 100) -> TicketPage:
        capped = max(1, min(int(page_size), 100))
        ps = capped
        async with Railengine(model=SupportTicket) as client:
            page = await client.list_storage_documents(
                page_number=page_number,
                page_size=ps,
            )

        tickets = _collect_tickets(page.items)

        return TicketPage(
            items=tickets,
            total_pages=getattr(page, "total_pages", 0) or 0,
            total_count=getattr(page, "total_count", len(tickets)),
            page_number=getattr(page, "page_number", page_number),
            page_size=getattr(page, "page_size", ps),
        )

    async def list_all(self, *, page_size: int = 100) -> list[SupportTicket]:
        """Walk every storage page in one Railengine session; return parsed tickets."""
        capped = max(1, min(int(page_size), 100))
        out: list[SupportTicket] = []
        async with Railengine(model=SupportTicket) as client:
            pn = 1
            while True:
                page = await client.list_storage_documents(
                    page_number=pn,
                    page_size=capped,
                )
                out.extend(_collect_tickets(page.items))
                total_pages = getattr(page, "total_pages", 0) or 0
                if total_pages < 1 or pn >= total_pages:
                    break
                pn += 1
        return out

    async def search_index_hits(self, query: str, limit: int) -> list[SupportTicket]:
        out: list[SupportTicket] = []
        async with Railengine(model=SupportTicket) as client:
            result = await client.search_index(query={"search": query}, raw=False)
            for item in result.items:
                t = _as_ticket(item)
                if t is not None:
                    out.append(t)
                if len(out) >= limit:
                    break
        return out

    async def search_vector_hits(self, query: str, limit: int) -> list[SupportTicket]:
        out: list[SupportTicket] = []
        async with Railengine(model=SupportTicket) as client:
            items = await client.search_vector_store(
                vector_store="VectorStore1",
                query=query,
                top=limit,
            )
        for item in items:
            t = _as_ticket(item)
            if t is not None:
                out.append(t)
            if len(out) >= limit:
                break
        return out

    async def query_jsonpath_tickets(self, jq: str) -> list[SupportTicket]:
        async with Railengine(model=SupportTicket) as client:
            page = await client.query_storage_by_jsonpath(json_path_query=jq)
        return _collect_tickets(page.items)

    async def iter_storage_tickets(
        self,
        *,
        page_size: int,
        max_docs: int,
    ) -> AsyncIterator[SupportTicket]:
        """Yield parsed tickets from storage pages until ``max_docs`` or pages exhausted."""
        async with Railengine(model=SupportTicket) as client:
            scanned = 0
            pn = 1
            while scanned < max_docs:
                page = await client.list_storage_documents(
                    page_number=pn,
                    page_size=page_size,
                )
                for item in page.items:
                    t = _as_ticket(item)
                    if t is not None:
                        yield t
                    scanned += 1
                    if scanned >= max_docs:
                        return
                if page.total_pages < 1 or pn >= page.total_pages:
                    return
                pn += 1
