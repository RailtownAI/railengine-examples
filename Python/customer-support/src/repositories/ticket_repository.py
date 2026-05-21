"""Railengine ingest + retrieval I/O."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from railtown.engine import Railengine
from railtown.engine.ingest import RailengineIngest

from customer_support.models import SupportTicket, TicketPage
from customer_support.repositories.mappers import ticket_from_row


async def ingest_ticket_with_client(client: RailengineIngest, ticket: SupportTicket) -> int:
    """Upsert using an existing ingest client."""
    resp = await client.upsert(ticket)
    return resp.status_code


class TicketRepository:
    """SDK-backed ticket persistence and search."""

    async def upsert(self, ticket: SupportTicket) -> int:
        async with RailengineIngest(model=SupportTicket) as client:
            return await ingest_ticket_with_client(client, ticket)

    async def ingest_paths(self, paths: list[Path]) -> None:
        """Batch ingest preserving a single ingest session."""
        async with RailengineIngest(model=SupportTicket) as client:
            for path in paths:
                raw = json.loads(path.read_text(encoding="utf-8"))
                ticket = SupportTicket.model_validate(raw)
                status = await ingest_ticket_with_client(client, ticket)
                print(f"Ingested {path.name} -> HTTP {status}")

    async def list_page(self, page_number: int = 1, page_size: int = 100) -> TicketPage:
        capped = max(1, min(int(page_size), 100))
        ps = capped
        async with Railengine() as client:
            page = await client.list_storage_documents(
                page_number=page_number,
                page_size=ps,
                raw=True,
            )

        tickets: list[SupportTicket] = []
        for row in page.items:
            t = ticket_from_row(row)
            if t:
                tickets.append(t)

        return TicketPage(
            items=tickets,
            total_pages=getattr(page, "total_pages", 0) or 0,
            total_count=getattr(page, "total_count", len(tickets)),
            page_number=getattr(page, "page_number", page_number),
            page_size=getattr(page, "page_size", ps),
        )

    async def search_index_hits(self, query: str, limit: int) -> list[SupportTicket]:
        out: list[SupportTicket] = []
        async with Railengine() as client:
            result = await client.search_index(query={"search": query}, raw=True)
            for row in result.items:
                t = ticket_from_row(row)
                if t:
                    out.append(t)
                if len(out) >= limit:
                    break
        return out

    async def search_vector_hits(self, query: str, limit: int) -> list[SupportTicket]:
        out: list[SupportTicket] = []
        async with Railengine() as client:
            items = await client.search_vector_store(
                vector_store="VectorStore1",
                query=query,
                top=limit,
            )
        for row in items:
            t = ticket_from_row(row)
            if t:
                out.append(t)
            if len(out) >= limit:
                break
        return out

    async def query_jsonpath_tickets(self, jq: str) -> list[SupportTicket]:
        async with Railengine() as client:
            page = await client.query_storage_by_jsonpath(json_path_query=jq)
        collected: list[SupportTicket] = []
        for row in page.items:
            t = ticket_from_row(row)
            if t:
                collected.append(t)
        return collected

    async def iter_raw_storage_pages(
        self,
        *,
        page_size: int,
        max_docs: int,
    ) -> AsyncIterator[Any]:
        """Yield raw rows until ``max_docs`` or pages exhausted (single session)."""
        async with Railengine() as client:
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
