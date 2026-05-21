"""Support ticket document (Railengine schema)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SupportTicket(BaseModel):
    """Document shape stored in Railengine (matches engine-schema sample)."""

    id: str = Field(..., description="Stable ticket id / business key")
    subject: str
    body: str
    status: Literal["open", "pending", "resolved"]
    tags: list[str] = Field(default_factory=list)
    createdAt: str
    customerEmail: str = ""
    customerPhone: str = ""
    productArea: str = ""
