"""Paginated storage list orchestration."""

from __future__ import annotations

from customer_support.models import TicketPage
from customer_support.repositories import TicketRepository


class TicketListService:
    """Expose ``list_storage_documents`` as a TicketPage."""

    def __init__(self, repository: TicketRepository | None = None) -> None:
        self._repo = repository or TicketRepository()

    async def fetch_page(self, page_number: int = 1, page_size: int = 50) -> TicketPage:
        return await self._repo.list_page(page_number=page_number, page_size=page_size)
