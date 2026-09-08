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

BIND (2026-09-08): defaults to 127.0.0.1, was 0.0.0.0. The wide bind came from the bare
`http.server ... --bind 0.0.0.0` this replaced, not from a decision — and `serve_harness.sh`
only ever health-checks 127.0.0.1. It mattered because the doc root is the WHOLE site tree,
including everything `escape_rooms/.gitignore` deliberately keeps off the public site: per-
scenario `notes.md`, `AGENTS.md`, `_scratch/`, `scenario.json.bak`, and the `designNotes` /
`plannedHotspots` blocks that hold the MCQ ANSWER KEYS for graded CHEM 5725 exercises. On a
box with a routable campus IP that was an unauthenticated directory listing of the answers.

To playtest from another device on the LAN (phone, iPad), set the bind explicitly:
    PLAYTEST_BIND=0.0.0.0 python3 playtest_server.py 8055
Prefer an SSH tunnel where you can: `ssh -L 8055:localhost:8055 bustalab@131.212.57.217`.
"""
import http.server
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8055
BIND = os.environ.get("PLAYTEST_BIND", "127.0.0.1")


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
    with Server((BIND, PORT), NoStoreHandler) as httpd:
        print(f"playtest server (no-store) serving cwd on {BIND}:{PORT}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
