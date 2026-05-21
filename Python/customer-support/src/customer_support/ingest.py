"""Load fixtures into Railengine via rail-engine-ingest."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from railtown.engine.ingest import RailengineIngest

from customer_support._env import ensure_dotenv_loaded
from customer_support.models import SupportTicket


async def ingest_ticket_with_client(client: RailengineIngest, ticket: SupportTicket) -> int:
    """Upsert using an existing ingest client."""
    resp = await client.upsert(ticket)
    return resp.status_code


async def ingest_ticket(ticket: SupportTicket) -> int:
    """Upsert a single ticket (opens its own ingest client/session)."""
    async with RailengineIngest(model=SupportTicket) as client:
        return await ingest_ticket_with_client(client, ticket)


async def ingest_paths(paths: list[Path]) -> None:
    async with RailengineIngest(model=SupportTicket) as client:
        for p in paths:
            raw = json.loads(p.read_text(encoding="utf-8"))
            ticket = SupportTicket.model_validate(raw)
            status = await ingest_ticket_with_client(client, ticket)
            print(f"Ingested {p.name} -> HTTP {status}")


def main_sync() -> None:
    ensure_dotenv_loaded()
    parser = argparse.ArgumentParser(
        description="Upsert support ticket JSON fixtures into Railengine.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Fixture paths (e.g. fixtures/tickets/*.json)",
    )
    args = parser.parse_args()
    paths = [Path(f) for f in args.files]
    asyncio.run(ingest_paths(paths))


def main() -> None:
    main_sync()


if __name__ == "__main__":
    main()
