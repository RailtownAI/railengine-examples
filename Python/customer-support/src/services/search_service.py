"""Railengine index search orchestration."""

from __future__ import annotations

from customer_support.models import SupportTicket
from customer_support.repositories import TicketRepository


class SearchService:
    """Expose ``search_index`` for keyword retrieval."""

    def __init__(self, repository: TicketRepository | None = None) -> None:
        self._repo = repository or TicketRepository()

    async def search_index(self, query: str, *, limit: int = 50) -> list[SupportTicket]:
        capped = max(1, min(int(limit), 100))
        return await self._repo.search_index_hits(query, capped)
