"""
Optional local webhook receiver for Railengine publishing (activation demo).

Run::

    uv run python -m customer_support.controllers.webhook --port 8765

Point your engine webhook URL at http://localhost:8765/webhook (use ngrok or similar for a public URL).

The handler parses `WebhookPublishingPayload` bodies using the same ``SupportTicket`` model as ingest.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from railtown.engine.ingest import WebhookHandler

from customer_support.config.env import ensure_dotenv_loaded
from customer_support.models import SupportTicket


class Handler(BaseHTTPRequestHandler):
    model_handler = WebhookHandler(SupportTicket)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[webhook] {self.address_string()} - {format % args}")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/webhook":
            self.send_error(404, "Not Found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(raw_body) if raw_body.strip() else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        try:
            events = self.model_handler.parse(payload)
        except Exception as e:
            self.send_error(400, f"Parse error: {e}")
            return

        for ev in events:
            print(
                json.dumps(
                    {
                        "eventId": ev.EventId,
                        "ticketId": ev.body.id,
                        "subject": ev.body.subject,
                        "status": ev.body.status,
                    },
                    indent=2,
                )
            )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')


def main() -> None:
    ensure_dotenv_loaded()
    parser = argparse.ArgumentParser(description="Receive Railengine webhook POSTs locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    httpd = HTTPServer((args.host, args.port), Handler)
    print(f"Listening on http://{args.host}:{args.port}/webhook (POST)", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)


if __name__ == "__main__":
    main()
