"""Ingest orchestration."""

from __future__ import annotations

from pathlib import Path

from customer_support.models import SupportTicket
from customer_support.repositories import TicketRepository


class IngestService:
    """Use-case wrapper for fixture → Railengine ingest."""

    def __init__(self, repository: TicketRepository | None = None) -> None:
        self._repo = repository or TicketRepository()

    async def ingest_ticket(self, ticket: SupportTicket) -> int:
        """Upsert a single ticket."""
        return await self._repo.upsert(ticket)

    async def ingest_paths(self, paths: list[Path]) -> None:
        """Batch-ingest fixture files (single ingest session)."""
        await self._repo.ingest_paths(paths)
