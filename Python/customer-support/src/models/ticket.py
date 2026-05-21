"""Support ticket document (Railengine schema)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TicketStatus = Literal["pending", "open", "in_progress", "resolved"]

TICKET_STATUSES: tuple[TicketStatus, ...] = ("pending", "open", "in_progress", "resolved")

KANBAN_COLUMNS: tuple[tuple[str, TicketStatus], ...] = (
    ("Pending", "pending"),
    ("Open", "open"),
    ("In Progress", "in_progress"),
    ("Resolved", "resolved"),
)


class SupportTicket(BaseModel):
    """Document shape stored in Railengine (matches engine-schema sample)."""

    id: str = Field(..., description="Stable ticket id / business key")
    subject: str
    body: str
    status: TicketStatus = Field(...)
    tags: list[str] = Field(default_factory=list)
    createdAt: str
    customerEmail: str = ""
    customerPhone: str = ""
    productArea: str = ""
