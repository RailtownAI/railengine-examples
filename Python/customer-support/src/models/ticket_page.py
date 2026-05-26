"""Paging DTO for storage list."""

from __future__ import annotations

from dataclasses import dataclass

from customer_support.models.ticket import SupportTicket


@dataclass(frozen=True)
class TicketPage:
    """One page of tickets from Railengine storage list."""

    items: list[SupportTicket]
    total_pages: int
    total_count: int
    page_number: int
    page_size: int
