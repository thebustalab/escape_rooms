#!/usr/bin/env bash
# harness_launch.command — ONE-CLICK escape-room harness launcher, run FROM THE MAC.
#
# Run in Terminal (or double-click in Finder once it's executable: `chmod +x harness_launch.command`).
# It:
#   1. SSHes into host2 (the Linux desktop) and runs serve_harness.sh with HARNESS_RESTART=1 to
#      (re)start the servers FRESH (harness API :8751 + V2 image-pipeline harness :8752 + playtest :8055)
#      — so every launch picks up the latest code (server changes only take effect on a fresh process).
#   2. Opens ONE SSH tunnel mapping the Mac's own localhost:8751, :8752 and :8055 to host2's, so the Mac
#      sees all servers exactly where host2 does. That keeps the test-play flow's origins consistent
#      (the mixer on localhost:8055 posts volumes to the harness on localhost:8751 — same as on host2).
#   3. Opens the harness in the default browser.
#   4. HOLDS THE TERMINAL. Press Ctrl+C (or close the window) to TEAR THE WHOLE THING DOWN — the SSH
#      tunnel AND both host2 servers — so nothing is left running. The next launch then spins it all up
#      fresh. (Set KEEP_SERVERS=1 to leave the servers running on exit, the old behaviour.)
#
# Lifecycle in one line: each launch = fresh servers + tunnel; each Ctrl+C = full teardown.
#
# ── CONFIG ─────────────────────────────────────────────────────────────────────────────────────────
HOST2="${HARNESS_HOST:-bustalab@131.212.57.217}"      # override: HARNESS_HOST=bustalab@… ./harness_launch.command
SSH_OPTS="${HARNESS_SSH_OPTS:-}"                       # e.g. HARNESS_SSH_OPTS='-J host1'  if you must hop via host1
REMOTE_ENSURE="/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/authoring/serve_harness.sh"
URL="http://localhost:8751/harness_gpt.html"
# Dedicated control socket for OUR tunnel — kept separate from your ~/.ssh/config multiplexing so the
# tunnel can never silently attach to some other master connection (that was the "no tunnel" bug).
CTRL="$HOME/.ssh/cm-harness.sock"
# ────────────────────────────────────────────────────────────────────────────────────────────────────
set -u

# does the Mac's localhost:8751 actually reach the harness API? (the real end-to-end tunnel test)
tunnel_up() { curl -s -o /dev/null -m 2 "http://localhost:8751/api/scenarios"; }

echo "▶ escape-room harness launcher"
echo "  host2: $HOST2   ${SSH_OPTS:+(ssh opts: $SSH_OPTS)}"

# 1) ensure the servers are up on host2. ControlMaster=no: this call must NOT open/reuse a shared master
#    (which is what let the tunnel below no-op against an existing connection).
echo "① (re)starting servers FRESH on host2…"   # HARNESS_RESTART=1 → both servers relaunched so code changes take effect
if ! ssh $SSH_OPTS -o ControlMaster=no -o ConnectTimeout=8 "$HOST2" "HARNESS_RESTART=1 bash '$REMOTE_ENSURE'"; then
  echo "✗ couldn't reach host2 over SSH (or the ensure script failed)."
  echo "  Check you can run:  ssh $SSH_OPTS $HOST2   — on campus / VPN, key authorized on the desktop."
  echo "  If you must hop through host1:  HARNESS_SSH_OPTS='-J host1' $0"
  exit 1
fi

# 2) tunnel — reuse only if it genuinely reaches through; otherwise open a fresh dedicated-socket master
#    forwarding BOTH ports, then verify it actually came up (never assume).
#    WE_OPENED tracks whether THIS run created the tunnel, so cleanup only tears down what it owns.
WE_OPENED=0
if tunnel_up; then
  echo "② tunnel already up (localhost:8751 reaches the harness) — reusing (won't be torn down on exit)"
else
  ssh $SSH_OPTS -S "$CTRL" -O exit "$HOST2" 2>/dev/null  # clear any stale/dead master on our socket
  echo "② opening SSH tunnel  localhost:8751→host2 + localhost:8752→host2 + localhost:8055→host2 …"
  ssh $SSH_OPTS -M -S "$CTRL" -f -N \
      -L 8751:localhost:8751 \
      -L 8752:localhost:8752 \
      -L 8055:localhost:8055 \
      -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 "$HOST2"
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "✗ tunnel command exited $rc — most likely local :8751, :8752 or :8055 is already bound by something else."
    echo "  Inspect:  lsof -nP -iTCP:8751 -sTCP:LISTEN ;  lsof -nP -iTCP:8752 -sTCP:LISTEN ;  lsof -nP -iTCP:8055 -sTCP:LISTEN"
    exit 1
  fi
  for _ in 1 2 3 4 5; do tunnel_up && break; sleep 1; done
  if ! tunnel_up; then
    echo "✗ tunnel opened but localhost:8751 still can't reach the harness."
    echo "  Check the master:  ssh -S '$CTRL' -O check '$HOST2'"
    exit 1
  fi
  WE_OPENED=1
  echo "   tunnel verified ✓"
fi

# Cleanup runs on Ctrl+C (INT), termination (TERM/HUP — e.g. closing the window), and normal exit.
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
  # Full teardown by default (2026-07-28, Lucas): Ctrl+C / closing the window stops BOTH host2 servers, not
  # just the tunnel — so nothing is left running and the next launch spins everything up fresh. Set
  # KEEP_SERVERS=1 to leave them up (the old behaviour) if you ever want a launch to not tear them down.
  if [ "${KEEP_SERVERS:-0}" = 1 ]; then
    echo "⏹ leaving host2 servers running (KEEP_SERVERS=1)."
  else
    echo "⏹ stopping host2 servers…"
    ssh $SSH_OPTS -o ControlMaster=no -o ConnectTimeout=8 "$HOST2" \
        "tmux send-keys -t harness_ui C-c 2>/dev/null; tmux send-keys -t harness_v2 C-c 2>/dev/null; tmux send-keys -t playtest C-c 2>/dev/null" \
        && echo "   servers stopped ✓" || echo "   (couldn't reach host2 to stop servers)"
  fi
  echo "bye."
}
trap 'cleanup; exit 0' INT TERM HUP
trap cleanup EXIT

# 3) open the harness in the browser
echo "③ opening $URL"
open "$URL" 2>/dev/null || echo "  (open the URL manually: $URL)"

echo "✓ ready. Harness: $URL   ·   V2 harness: http://localhost:8752/harness_gpt.html   ·   test-play server: http://localhost:8055/"
echo "  Holding the tunnel open. Press Ctrl+C (or close this window) to close it and exit."

# 4) HOLD — keep the terminal (and the tunnel) alive until Ctrl+C. If the tunnel drops on its own
#    (network blip, host2 reboot), notice and exit rather than pretending it's still up.
while :; do
  sleep 5 &                    # backgrounded sleep so the INT signal interrupts the wait promptly
  wait $!
  if [ "$WE_OPENED" = 1 ] && ! ssh $SSH_OPTS -S "$CTRL" -O check "$HOST2" 2>/dev/null; then
    echo "✗ tunnel master went away — exiting."
    break
  fi
  if [ "$WE_OPENED" != 1 ] && ! tunnel_up; then
    echo "✗ reused tunnel is no longer reachable — exiting."
    break
  fi
done
