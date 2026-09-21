#!/usr/bin/env bash
# harness_launch.command — ONE-CLICK escape-room harness CONNECTOR, run FROM THE MAC.
#
# Lifecycle in one line: the servers live on host2 permanently (cron watchdog); this only connects —
# ensure-up, tunnel, open the console — and Ctrl+C / closing the laptop closes ONLY the tunnel it opened.
#
# Run in Terminal (or double-click in Finder; it must stay executable: `chmod +x harness_launch.command`).
#   1. SSHes into host2 and runs serve_harness.sh ENSURE-ONLY (no restart): a healthy server is left alone,
#      a missing/wedged one is started. It never interrupts a running job.
#   2. Opens ONE SSH tunnel mapping the Mac's localhost:8752 (harness) and :8055 (playtest) to host2's.
#   3. Opens the review console (build_world_v3.html) in the default browser.
#   4. HOLDS THE TERMINAL until Ctrl+C / window close / tunnel drop, then closes the tunnel it opened.
#      The host2 servers are NEVER stopped from here.
#
#   ./harness_launch.command --restart   (or HARNESS_RESTART=1 ./harness_launch.command)
#      After the tunnel is up, asks the harness to restart itself via POST /api/restart-harness — the SAME
#      guarded path as the console's "Restart harness" button, so it REFUSES while a job or room_iterate
#      run is live. Use it to load new server code.
#
# ── CONFIG ─────────────────────────────────────────────────────────────────────────────────────────
# WHERE host2 IS (2026-09-20). Lab addresses are ~1-hour DHCP leases and they MOVE: host2 went
# .217 -> .181 that day (and took the dgx's old address), which broke this launcher until it was
# repointed. So resolve in three steps, cheapest first:
#   1. $HARNESS_HOST, if you set it
#   2. the `host2` ssh alias, if this machine has one with a real hostname behind it — on the lab
#      boxes `infrastructure/fabric/fabric_resolve.py` keeps that alias on the current address
#   3. host2's address as of 2026-09-20, as a last resort for the roaming Mac
# If step 3 starts failing, the lease moved again: run fabric_resolve.py (or ask an agent to) and
# prefer giving this Mac a `host2` ssh alias so step 2 does the work from then on.
HOST2="${HARNESS_HOST:-}"
if [ -z "$HOST2" ]; then
  if ssh -G host2 2>/dev/null | grep -qE '^hostname ([0-9]{1,3}\.){3}[0-9]{1,3}$'; then
    HOST2="host2"
  else
    HOST2="bustalab@131.212.57.181"
  fi
fi
SSH_OPTS="${HARNESS_SSH_OPTS:-}"                       # e.g. HARNESS_SSH_OPTS='-J host1'  if you must hop via host1
REMOTE_ENSURE="/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/authoring_v2/serve_harness.sh"
URL="http://localhost:8752/build_world_v3.html"   # the clip-review console (v3, 2026-09-15); v2 gallery and the full
                                                  # console stay reachable at their own URLs on the same server.
# Dedicated control socket for OUR tunnel — kept separate from your ~/.ssh/config multiplexing so the
# tunnel can never silently attach to some other master connection (that was the "no tunnel" bug).
CTRL="$HOME/.ssh/cm-harness.sock"
# ────────────────────────────────────────────────────────────────────────────────────────────────────
set -u

RESTART="${HARNESS_RESTART:-0}"
for arg in "$@"; do
  case "$arg" in
    --restart) RESTART=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "✗ unknown argument: $arg   (only --restart is accepted)"; exit 2 ;;
  esac
done

# does the Mac's localhost:8752 actually reach the harness API? (the real end-to-end tunnel test)
tunnel_up() { curl -s -o /dev/null -m 2 "http://localhost:8752/api/scenarios"; }

echo "▶ escape-room harness launcher"
echo "  host2: $HOST2   ${SSH_OPTS:+(ssh opts: $SSH_OPTS)}"

# 1) ensure the servers are up on host2. ControlMaster=no: this call must NOT open/reuse a shared master
#    (which is what let the tunnel below no-op against an existing connection).
#    Ensure-only: NO HARNESS_RESTART here, ever — a restart goes through the guarded endpoint below.
echo "① ensuring servers are up on host2 (no restart)…"
ensure_up() { ssh $SSH_OPTS -o ControlMaster=no -o ConnectTimeout=8 "$HOST2" "HARNESS_RESTART=0 bash '$REMOTE_ENSURE'"; }
if ! ensure_up; then
  # AUTOMATIC HOP VIA host1 (2026-09-20). host2 sits on the wired lab subnet; this Mac roams, and from
  # campus wifi / off site the direct route TIMES OUT (not "refused" — the packets are dropped in the
  # network, nothing is wrong with host2: host1 reaches its port 22 fine at the same moment). host1
  # answers on a PUBLIC DNS NAME, so jumping through it works from anywhere the Mac has a network.
  if [ -z "$SSH_OPTS" ]; then
    echo "  direct route to host2 failed — retrying through host1 (bustalab.d.umn.edu)…"
    SSH_OPTS="-J bustalab@bustalab.d.umn.edu"
    if ensure_up; then
      echo "  ✓ reached host2 via host1. Set HARNESS_SSH_OPTS='-J bustalab@bustalab.d.umn.edu' to skip the retry."
      HOPPED=1
    fi
  fi
fi
if [ "${HOPPED:-0}" != 1 ] && ! ensure_up; then
  echo "✗ couldn't reach host2 over SSH (or the ensure script failed)."
  echo "  Check you can run:  ssh $SSH_OPTS $HOST2   — on campus / VPN, key authorized on the desktop."
  echo "  A timeout (rather than 'refused') usually means the network, not the box: try the host1 hop,"
  echo "  HARNESS_SSH_OPTS='-J bustalab@bustalab.d.umn.edu' $0"
  exit 1
fi

# 2) tunnel — reuse only if it genuinely reaches through; otherwise open a fresh dedicated-socket master
#    forwarding BOTH ports, then verify it actually came up (never assume).
#    WE_OPENED tracks whether THIS run created the tunnel, so cleanup only tears down what it owns.
WE_OPENED=0
if tunnel_up; then
  echo "② tunnel already up (localhost:8752 reaches the harness) — reusing (won't be torn down on exit)"
else
  ssh $SSH_OPTS -S "$CTRL" -O exit "$HOST2" 2>/dev/null  # clear any stale/dead master on our socket
  echo "② opening SSH tunnel  localhost:8752→host2 + localhost:8055→host2 …"
  ssh $SSH_OPTS -M -S "$CTRL" -f -N \
      -L 8752:localhost:8752 \
      -L 8055:localhost:8055 \
      -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 "$HOST2"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "✗ tunnel command exited $rc — most likely local :8752 or :8055 is already bound by something else."
    echo "  Inspect:  lsof -nP -iTCP:8752 -sTCP:LISTEN ;  lsof -nP -iTCP:8055 -sTCP:LISTEN"
    exit 1
  fi
  for _ in 1 2 3 4 5; do tunnel_up && break; sleep 1; done
  if ! tunnel_up; then
    echo "✗ tunnel opened but localhost:8752 still can't reach the harness."
    echo "  Check the master:  ssh -S '$CTRL' -O check '$HOST2'"
    exit 1
  fi
  WE_OPENED=1
  echo "   tunnel verified ✓"
fi

# Cleanup runs on Ctrl+C (INT), termination (TERM/HUP — e.g. closing the window or the laptop lid), and
# normal exit. It closes ONLY the tunnel this run opened; the host2 servers are never touched (2026-09-17,
# Lucas: the old full teardown parked long-running art jobs whenever the laptop closed).
# Idempotent via CLEANED so the EXIT trap doesn't double-run after an INT/TERM.
CLEANED=0
cleanup() {
  [ "$CLEANED" = 1 ] && return
  CLEANED=1
  echo
  if [ "$WE_OPENED" = 1 ]; then
    echo "⏹ closing SSH tunnel…"
    ssh $SSH_OPTS -S "$CTRL" -O exit "$HOST2" 2>/dev/null && echo "   tunnel closed ✓" || echo "   (tunnel already down)"
  else
    echo "⏹ leaving the pre-existing tunnel in place (this run didn't open it)."
  fi
  echo "   host2 servers left running (they are persistent)."
  echo "bye."
}
trap 'cleanup; exit 0' INT TERM HUP
trap cleanup EXIT

# 2b) optional guarded restart — the same endpoint as the console button, so it refuses while anything
#     is live. The server replies at once and restarts ~1 s later; wait for it to go away and come back.
if [ "$RESTART" = 1 ]; then
  echo "↻ requesting a guarded harness restart…"
  rbody=$(mktemp -t harness_restart)
  code=$(curl -s -m 10 -o "$rbody" -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' \
         "http://localhost:8752/api/restart-harness")
  body=$(cat "$rbody"); rm -f "$rbody"
  if [ "$code" = 200 ]; then
    sleep 4
    for _ in $(seq 1 30); do tunnel_up && break; sleep 1; done
    tunnel_up && echo "   harness restarted ✓ (re-select your scenario: a restart resets it to the default)" \
              || echo "✗ harness did not come back within ~35 s — see ~/.local/state/escape_harness/restart.log on host2"
  elif [ "$code" = 404 ]; then
    echo "✗ this harness predates the restart endpoint. Once no art run is live, restart it by hand on host2:"
    echo "    HARNESS_RESTART=1 bash '$REMOTE_ENSURE'    (unguarded — check first)"
  else
    echo "✗ restart refused (HTTP $code): $body"
  fi
fi

# 3) open the harness in the browser
echo "③ opening $URL"
open "$URL" 2>/dev/null || echo "  (open the URL manually: $URL)"

echo "✓ ready. build_world: $URL   ·   test-play server: http://localhost:8055/"
echo "  Holding the tunnel open. Ctrl+C (or close this window) closes the tunnel only; servers keep running."

# 4) HOLD — keep the terminal (and the tunnel) alive until Ctrl+C. If the tunnel drops on its own
#    (network blip, host2 reboot), notice and exit rather than pretending it's still up.
MISSES=0                       # a reused tunnel blips while the harness restarts; exit only on a sustained drop
while :; do
  sleep 5 &                    # backgrounded sleep so the INT signal interrupts the wait promptly
  wait $!
  if [ "$WE_OPENED" = 1 ] && ! ssh $SSH_OPTS -S "$CTRL" -O check "$HOST2" 2>/dev/null; then
    echo "✗ tunnel master went away — exiting."
    break
  fi
  if [ "$WE_OPENED" != 1 ]; then
    if tunnel_up; then MISSES=0; else MISSES=$((MISSES + 1)); fi
    if [ "$MISSES" -ge 6 ]; then
      echo "✗ reused tunnel is no longer reachable — exiting."
      break
    fi
  fi
done
