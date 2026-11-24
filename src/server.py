"""HTTP service for the calculator module.

The process listens on 0.0.0.0:8080.
GET /health returns {"status": "ok"}.
GET /add?a=&b= returns the sum as JSON.
A missing or invalid number returns HTTP 400.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from src.calculator import add

HOST = "0.0.0.0"
PORT = 8080

_INTEGER = re.compile(r"[+-]?\d+")


def parse_number(raw):
    """Return int or float. Raise ValueError when raw is not a finite number."""
    if raw is None:
        raise ValueError("missing number")
    text = str(raw).strip()
    if text == "":
        raise ValueError("empty number")
    if _INTEGER.fullmatch(text):
        return int(text)
    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError("invalid number") from exc
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("invalid number")
    return value


class AppHandler(BaseHTTPRequestHandler):
    """Handlers for /health and /add."""

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if parsed.path == "/add":
            self._handle_add(parsed.query)
            return
        self._send_json(404, {"error": "not found"})

    def _handle_add(self, query):
        params = parse_qs(query, keep_blank_values=True)
        try:
            left = parse_number((params.get("a") or [None])[0])
            right = parse_number((params.get("b") or [None])[0])
        except ValueError:
            self._send_json(400, {"error": "invalid number"})
            return
        self._send_json(
            200,
            {"a": left, "b": right, "result": add(left, right)},
        )


def make_server(host=HOST, port=PORT):
    """Create the HTTP server. Tests pass port 0 to bind an ephemeral port."""
    return ThreadingHTTPServer((host, port), AppHandler)


def main():
    """Listen on 0.0.0.0:8080 until the process is stopped."""
    server = make_server()
    print(f"Listening on {HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
