#!/usr/bin/env python3
"""playtest_server.py — static server for the escape-room test-play flow on :8055.

Drop-in replacement for a bare `python3 -m http.server 8055 --bind 0.0.0.0`: it serves
the site doc root exactly the same, but sends `Cache-Control: no-store` on every
response so an authoring browser NEVER serves a stale cached engine.

WHY THIS EXISTS (2026-08-05). The playtest server was stock `http.server`, which sends
no cache-control and lets the browser heuristically cache static files. After an edit to
`shared/pano-player.js` WITHOUT bumping the `?v=` cache-buster in the `play.html` shells,
browsers kept the OLD engine under the same `?v=` URL: `play.html` pages rendered blank
and an `endsEscape` door did nothing, while a fresh private window (empty cache) worked
— the classic "works in incognito" tell. `no-store` makes the dev harness always fresh
so a `?v=` bump is no longer load-bearing during authoring. (The authoring server on
:8751, `harness_server.py`, already sends `no-cache` — this brings :8055 in line.)

The `?v=` scheme still protects the PRODUCTION GitHub Pages cache; this only changes the
local playtest server. Started by `serve_harness.sh` in the `playtest` tmux session.
"""
import http.server
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8055


class NoStoreHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # kill every layer of caching so the browser always refetches the current bytes
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("0.0.0.0", PORT), NoStoreHandler) as httpd:
        print(f"playtest server (no-store) serving cwd on 0.0.0.0:{PORT}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
