"""Domain models."""

from customer_support.models.ticket import SupportTicket
from customer_support.models.ticket_page import TicketPage
from customer_support.models.triage import TriageAssessment

__all__ = ["SupportTicket", "TicketPage", "TriageAssessment"]
