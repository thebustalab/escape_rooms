#!/usr/bin/env bash
# serve_harness.sh — ensure the escape-room authoring stack is up on host2 (bustalab-desktop).
#
# Three servers, each in its own persistent tmux session:
#   harness_ui  -> harness_server.py             on 127.0.0.1:8751  (authoring UI + /api, localhost-only)
#   harness_v2  -> authoring_v2/harness_server.py on 127.0.0.1:8752  (V2 image-pipeline harness; non-fatal)
#   playtest    -> python -m http.server 8055    on 0.0.0.0:8055     (serves the site root for test-play)
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
HARNESS="$SITE/escape_rooms/authoring/harness_server.py"
HARNESS_V2="$SITE/escape_rooms/authoring_v2/harness_server.py"     # V2 image-pipeline harness, binds :8752

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

# Free a TCP port before a (re)start: kill any process LISTENing on it. Without this, a STRAY harness
# started outside tmux (e.g. a manual `python3 harness_server.py` in a non-interactive shell that has NO
# OPENAI_API_KEY) keeps holding the port, so the tmux (re)launch can't bind and silently drops to an idle
# shell — leaving the keyless stray serving, and every gen failing with "OPENAI_API_KEY not set" (2026-07-31).
free_port() {                                                     # <port>
  local pids; pids=$(ss -ltnpH "sport = :$1" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u)
  [ -n "$pids" ] && { echo "  freeing :$1 (killing stray $(echo $pids))"; kill $pids 2>/dev/null; sleep 1; }
  return 0
}

# --- harness API on :8751 ---
if [ "$FORCE_RESTART" != 1 ] && answers "http://127.0.0.1:8751/api/scenarios"; then
  echo "harness  :8751  already up"
else
  [ "$FORCE_RESTART" = 1 ] && echo "harness  :8751  force-restarting (fresh) in tmux 'harness_ui'…" || echo "harness  :8751  (re)starting in tmux 'harness_ui'…"
  free_port 8751
  restart_in harness_ui "python3 '$HARNESS'"
fi

# --- harness V2 (image-pipeline upgrades) on :8752 ---
if [ "$FORCE_RESTART" != 1 ] && answers "http://127.0.0.1:8752/api/scenarios"; then
  echo "harness2 :8752  already up"
else
  [ "$FORCE_RESTART" = 1 ] && echo "harness2 :8752  force-restarting (fresh) in tmux 'harness_v2'…" || echo "harness2 :8752  (re)starting in tmux 'harness_v2'…"
  free_port 8752
  restart_in harness_v2 "python3 '$HARNESS_V2'"
fi

# --- playtest static server on :8055 ---
if [ "$FORCE_RESTART" != 1 ] && answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"; then
  echo "playtest :8055  already up"
else
  [ "$FORCE_RESTART" = 1 ] && echo "playtest :8055  force-restarting (fresh) in tmux 'playtest'…" || echo "playtest :8055  (re)starting in tmux 'playtest'…"
  restart_in playtest "cd '$SITE' && python3 -m http.server 8055 --bind 0.0.0.0"
fi

# --- settle + report ---
sleep 2
ok=1
answers "http://127.0.0.1:8751/api/scenarios"                        && echo "  ✓ harness   http://localhost:8751/harness_gpt.html" || { echo "  ✗ harness  not answering on :8751"; ok=0; }
answers "http://127.0.0.1:8752/api/scenarios"                        && echo "  ✓ harness2  http://localhost:8752/harness_gpt.html" || echo "  ⚠ harness2 not answering on :8752 (V2, non-fatal)"
answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"   && echo "  ✓ playtest  http://localhost:8055/"                    || { echo "  ✗ playtest not answering on :8055"; ok=0; }
exit $((1 - ok))
