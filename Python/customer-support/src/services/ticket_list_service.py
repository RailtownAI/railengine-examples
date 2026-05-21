"""Paginated storage list orchestration."""

from __future__ import annotations

from customer_support.models import SupportTicket, TicketPage
from customer_support.repositories import TicketRepository


class TicketListService:
    """Expose ``list_storage_documents`` as a TicketPage."""

    def __init__(self, repository: TicketRepository | None = None) -> None:
        self._repo = repository or TicketRepository()

    async def fetch_page(self, page_number: int = 1, page_size: int = 50) -> TicketPage:
        return await self._repo.list_page(page_number=page_number, page_size=page_size)

    async def fetch_all(self, *, page_size: int = 100) -> list[SupportTicket]:
        """Full storage snapshot (paginated internally)."""
        return await self._repo.list_all(page_size=page_size)

    async def fetch_open_and_pending(self, *, page_size: int = 100) -> list[SupportTicket]:
        """Tickets in ``open`` or ``pending`` status for the triage queue."""
        tickets = await self.fetch_all(page_size=page_size)
        return [t for t in tickets if t.status in ("open", "pending")]
