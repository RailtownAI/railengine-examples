"""CLI: run Railtracks triage for one ticket fixture against live Railengine data."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from customer_support._env import ensure_dotenv_loaded
from customer_support.models import SupportTicket
from customer_support.triage_runner import triage_ticket


def main_sync() -> None:
    ensure_dotenv_loaded()
    parser = argparse.ArgumentParser(
        description="Run the Customer Support Triage agent for one ticket JSON file.",
    )
    parser.add_argument(
        "--ticket",
        type=Path,
        required=True,
        help="Path to ticket JSON (e.g. fixtures/tickets/ticket_001.json)",
    )
    args = parser.parse_args()

    if not args.ticket.is_file():
        print(f"File not found: {args.ticket}", file=sys.stderr)
        sys.exit(1)

    try:
        raw = json.loads(args.ticket.read_text(encoding="utf-8"))
        ticket = SupportTicket.model_validate(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid ticket JSON syntax: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Invalid ticket JSON: {e}", file=sys.stderr)
        sys.exit(1)

    assessment = asyncio.run(triage_ticket(ticket))
    print(json.dumps(assessment.model_dump(), indent=2, ensure_ascii=False))


def main() -> None:
    main_sync()


if __name__ == "__main__":
    main()
