#!/usr/bin/env bash
# serve_harness.sh — ensure the escape-room authoring stack is up on host2 (bustalab-desktop).
#
# Two servers, each in its own persistent tmux session:
#   harness_ui  -> harness_server.py           on 127.0.0.1:8751  (authoring UI + /api, localhost-only)
#   playtest    -> python -m http.server 8055  on 0.0.0.0:8055     (serves the site root for test-play)
#
# Idempotent: a server already answering is left ALONE; only a missing/wedged one is (re)started in
# its session. Safe to run repeatedly. Meant to be called locally on host2, or over SSH from the Mac
# launcher (harness_launch.command). Prints a status line per server and the URLs at the end.
set -u

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

answers() { curl -s -o /dev/null -m 2 "$1"; }                      # 0 if the URL responds at all
ensure_session() { tmux has-session -t "$1" 2>/dev/null || tmux new-session -d -s "$1"; }

# (Re)start a server inside its tmux session: Ctrl-C whatever's there, then launch. `bash -lic` so the
# conda base python3 (the one already serving these) resolves in a fresh session too.
restart_in() {                                                    # <session> <command>
  ensure_session "$1"
  tmux send-keys -t "$1" C-c 2>/dev/null
  sleep 1
  tmux send-keys -t "$1" "bash -lic \"$2\"" Enter
}

# --- harness API on :8751 ---
if answers "http://127.0.0.1:8751/api/scenarios"; then
  echo "harness  :8751  already up"
else
  echo "harness  :8751  (re)starting in tmux 'harness_ui'…"
  restart_in harness_ui "python3 '$HARNESS'"
fi

# --- playtest static server on :8055 ---
if answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"; then
  echo "playtest :8055  already up"
else
  echo "playtest :8055  (re)starting in tmux 'playtest'…"
  restart_in playtest "cd '$SITE' && python3 -m http.server 8055 --bind 0.0.0.0"
fi

# --- settle + report ---
sleep 2
ok=1
answers "http://127.0.0.1:8751/api/scenarios"                        && echo "  ✓ harness   http://localhost:8751/harness_gpt.html" || { echo "  ✗ harness  not answering on :8751"; ok=0; }
answers "http://127.0.0.1:8055/escape_rooms/shared/test_play.html"   && echo "  ✓ playtest  http://localhost:8055/"                    || { echo "  ✗ playtest not answering on :8055"; ok=0; }
exit $((1 - ok))
