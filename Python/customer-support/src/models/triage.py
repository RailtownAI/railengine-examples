"""Structured triage output from the Railtracks agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TriageAssessment(BaseModel):
    """Structured triage output from the Railtracks agent."""

    priority: Literal["p1", "p2", "p3", "p4"] = Field(
        ...,
        description="p1 critical outage / legal; p2 major customer pain; p3 normal; p4 low",
    )
    category: str = Field(..., description="Short category label, e.g. billing, auth")
    internal_summary: str = Field(
        ...,
        description="Internal 2–4 sentence summary for support leads (no raw secrets).",
    )
    draft_reply_to_customer: str = Field(
        ...,
        description="Empathetic draft reply. Do not repeat suspected secrets or API keys.",
    )
    similar_ticket_ids: list[str] = Field(
        default_factory=list,
        description="Ids of similar historical tickets found via search tools",
    )
    reasoning: str = Field(
        ...,
        description="Brief justification for priority and category",
    )
