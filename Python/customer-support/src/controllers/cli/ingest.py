"""CLI: ingest ticket fixtures."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from customer_support.config.env import ensure_dotenv_loaded
from customer_support.services.ingest_service import IngestService


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
    asyncio.run(IngestService().ingest_paths(paths))


def main() -> None:
    main_sync()


if __name__ == "__main__":
    main()
