"""Serve public/ locally with the same response headers that vercel.json sets.

Usage: python3 scripts/serve.py [port]
"""

import functools
import http.server
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "vercel.json").read_text())
HEADERS = [
    (h["key"], h["value"])
    for rule in CONFIG["headers"]
    if rule["source"] == "/(.*)" and "has" not in rule
    for h in rule["headers"]
]


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".webmanifest": "application/manifest+json",
    }

    def send_head(self):
        """Clean URLs like Vercel: /gil serves gil.html and /ro serves ro/index.html."""
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        rel = path.strip("/")
        root = Path(self.directory)
        if rel and not Path(rel).suffix and (root / f"{rel}.html").is_file():
            self.path = f"/{rel}.html"
        elif rel and (root / rel / "index.html").is_file():
            self.path = f"/{rel}/index.html"
        return super().send_head()

    def end_headers(self):
        for key, value in HEADERS:
            self.send_header(key, value)
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def make_server(port=8000):
    handler = functools.partial(Handler, directory=str(ROOT / "public"))
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    with make_server(port) as httpd:
        print(f"Serving http://127.0.0.1:{port}/ with the headers from vercel.json")
        httpd.serve_forever()
