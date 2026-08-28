#!/usr/bin/env bash
# serve_harness.sh — ensure the escape-room authoring stack is up on host2 (bustalab-desktop).
#
# Two servers, each in its own persistent tmux session:
#   harness_v2  -> authoring_v2/harness_server.py  on 127.0.0.1:8752  (build_world console + /api)
#   playtest    -> authoring/playtest_server.py    on 0.0.0.0:8055     (site root for test-play, no-store)
#
# The old v1 harness on :8751 (authoring/harness_server.py + harness_gpt.html) is NO LONGER STARTED
# (2026-08-28, Lucas: "it should only open the build_world stuff — the other stuff is obsolete"). The
# v1 code is left on disk rather than deleted; nothing launches it. Everything the console needs is
# served from :8752, and test-play links carry `harness=<origin>`, so the mixer posts back to :8752
# with no hard-coded port anywhere.
#
# Idempotent by default: a server already answering is left ALONE; only a missing/wedged one is
# (re)started in its session. Safe to run repeatedly. Meant to be called locally on host2, or over SSH
# from the Mac launcher (harness_launch.command). Prints a status line per server and the URLs at the end.
#
# HARNESS_RESTART=1 forces a FRESH restart of BOTH servers even if they're already up — so a new
# `python3 harness_server.py` process picks up code changes (e.g. the no-cache headers). The launcher
# passes this on every run so each launch spins everything up fresh.
set -u
FORCE_RESTART="${HARNESS_RESTART:-0}"

# Wrong-machine guard. This manages tmux sessions that live on host2 (the Linux desktop); it must run
# THERE, not on the Mac (whose Tools/ is a Syncthing copy, so this file exists here too — tempting to
# run, but there's no tmux and no servers). From the Mac use harness_launch.command instead, which
# SSHes into host2 and calls this. Override for an unusual host with HARNESS_FORCE_LOCAL=1.
if [ -z "${HARNESS_FORCE_LOCAL:-}" ] && ! command -v tmux >/dev/null 2>&1; then
  echo "✗ serve_harness.sh runs on host2 (the Linux desktop), not on $(hostname) — no tmux here."
  echo "  From the Mac, run:  ./harness_launch.command   (it SSHes into host2 and calls this for you)."
  exit 2
fi

TOOLS="/home/bustalab/Documents/Tools"
SITE="$TOOLS/websites/thebustalab.github.io"                       # doc root: /escape_rooms/... resolves here
HARNESS_V2="$SITE/escape_rooms/authoring_v2/harness_server.py"
PLAYTEST="$SITE/escape_rooms/authoring_v2/playtest_server.py"          # no-store, so no stale bytes locally

answers() { curl -s -o /dev/null -m 2 "$1"; }                      # 0 if the URL responds at all

# (Re)start a server in its OWN tmux session, robustly. We KILL any existing session and CREATE a fresh
# one already RUNNING the command — rather than creating an idle shell and send-keys'ing into it. That
# send-keys path raced/failed over non-interactive SSH when the session had to be created ("can't find
# pane: playtest", 2026-07-28). `bash -lic` so conda-base python3 resolves; `exec bash -l` after keeps the
# pane alive as a prompt if the server ever exits (so a crash leaves something inspectable, not a dead
# session). tmux runs the arg via `/bin/sh -c`, so the escaped double-quotes wrap the whole inner command.
restart_in() {                                                    # <session> <command>
  tmux kill-session -t "$1" 2>/dev/null
  tmux new-session -d -s "$1" "bash -lic \"$2 ; exec bash -l\""
}

# --- build_world harness on :8752 ---
if [ "$FORCE_RESTART" != 1 ] && answers "http://127.0.0.1:8752/api/scenarios"; then
  echo "harness  :8752  already up"
else
  [ "$FORCE_RESTART" = 1 ] && echo "harness  :8752  force-restarting (fresh) in tmux 'harness_v2'…" || echo "harness  :8752  (re)starting in tmux 'harness_v2'…"
  restart_in harness_v2 "python3 '$HARNESS_V2'"
fi

# --- playtest static server on :8055 ---
if [ "$FORCE_RESTART" != 1 ] && answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"; then
  echo "playtest :8055  already up"
else
  [ "$FORCE_RESTART" = 1 ] && echo "playtest :8055  force-restarting (fresh) in tmux 'playtest'…" || echo "playtest :8055  (re)starting in tmux 'playtest'…"
  restart_in playtest "cd '$SITE' && python3 '$PLAYTEST' 8055"
fi

# --- settle + report ---
sleep 2
ok=1
answers "http://127.0.0.1:8752/api/scenarios"                        && echo "  ✓ harness   http://localhost:8752/build_world.html" || { echo "  ✗ harness  not answering on :8752"; ok=0; }
answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"   && echo "  ✓ playtest  http://localhost:8055/"                    || { echo "  ✗ playtest not answering on :8055"; ok=0; }
exit $((1 - ok))
