"""Repository layer."""

from customer_support.repositories.ticket_repository import TicketRepository, ingest_ticket_with_client

__all__ = ["TicketRepository", "ingest_ticket_with_client"]
