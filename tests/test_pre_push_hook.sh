#!/usr/bin/env bash
#
# Regression test for githooks/pre-push (the oversize-blob push guard).
#
# FAILURE MODE IT PINS (2026-08-31)
# ---------------------------------
# A stage-everything commit swept authoring_v2/ui/cine360/ into the repo — the
# 360-cinemagraph parameter-sweep bench: 325 experiment clips, 2.1 GB, three boomerangs
# at 153-157 MB. Nothing there is play-required; no scenario.json references it.
#
# GitHub warns over 50 MB and REJECTS over 100 MB, and the rejection lands in its
# pre-receive hook — so the whole push died, taking ~500 legitimate room files with it,
# after 1.85 GB had already gone over the wire. The naive local check people reach for,
# `find . -size +50M`, is wrong twice over: it ignores .gitignore (flags files git will
# never send) and it reads the working tree (misses an oversize blob committed and then
# deleted in a later unpushed commit — still in the pushed history, still fatal).
#
# githooks/pre-push therefore walks the OBJECTS in the push range via
# `git rev-list --objects | git cat-file --batch-check`, not the filesystem.
#
# WHAT THIS TEST ASSERTS
#   1. oversize blob in the range          -> exit 1, names the file
#   2. oversize blob deleted in a LATER
#      unpushed commit (still in history)  -> exit 1  (the case `git ls-files` misses)
#   3. 50-100 MB blob                      -> warns, but does not block
#   4. clean range                         -> exit 0, silent
#   5. brand-new branch (no remote ref)    -> exit 0, and does not choke on the all-zero sha
#   6. ref deletion (all-zero local sha)   -> exit 0, skipped
#   7. SKIP_SIZE_CHECK=1                   -> exit 0, bypassed
#   8-11. the GRADING GATE wiring (2026-09-25): a failing gate blocks and names its bypass, a passing
#      one lets the push through, SKIP_GRADING_GATE=1 bypasses it, and — the regression that matters —
#      SKIP_SIZE_CHECK=1 no longer bypasses it, because the hook's two jobs are now independent.
#
# Run:  bash tests/test_pre_push_hook.sh
# Sparse files (truncate -s) keep this fast: git records the real size, packs to nothing.

set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/githooks/pre-push"
ZERO=0000000000000000000000000000000000000000
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
check() {  # check <name> <expected_exit> <actual_exit> [<output> <must_contain>]
    local name=$1 want=$2 got=$3 out=${4:-} needle=${5:-}
    if [ "$want" != "$got" ]; then
        echo "FAIL: $name — expected exit $want, got $got"; fail=$((fail+1)); return
    fi
    if [ -n "$needle" ] && ! printf '%s' "$out" | grep -q -- "$needle"; then
        echo "FAIL: $name — output missing '$needle'"; fail=$((fail+1)); return
    fi
    echo "ok: $name"; pass=$((pass+1))
}

new_repo() {  # new_repo <name> -> echoes worktree path, with origin/main already pushed
    local n=$1
    git init -q "$TMP/$n"
    git init -q --bare "$TMP/$n.git"
    git -C "$TMP/$n" config user.email t@t
    git -C "$TMP/$n" config user.name t
    git -C "$TMP/$n" remote add origin "$TMP/$n.git"
    echo base > "$TMP/$n/base.txt"
    git -C "$TMP/$n" add base.txt
    git -C "$TMP/$n" commit -qm base
    git -C "$TMP/$n" push -q origin HEAD:refs/heads/main
    git -C "$TMP/$n" fetch -q origin
    echo "$TMP/$n"
}

run_hook() {  # run_hook <repo> <local_sha> <remote_sha>; sets OUT, RC
    OUT=$( (cd "$1" && echo "refs/heads/main $2 refs/heads/main $3" | bash "$HOOK" origin fake-url) 2>&1 )
    RC=$?
}

# --- 1 + 3: oversize blocks, mid-size warns -------------------------------------
R=$(new_repo oversize)
truncate -s 101M "$R/big.mp4"; truncate -s 60M "$R/medium.mp4"
git -C "$R" add big.mp4 medium.mp4; git -C "$R" commit -qm oversize
run_hook "$R" "$(git -C "$R" rev-parse HEAD)" "$(git -C "$R" rev-parse origin/main)"
check "oversize blob blocks the push"       1 "$RC" "$OUT" "big.mp4"
check "block message names the 100 MB limit" 1 "$RC" "$OUT" "100 MB hard limit"
check "50-100 MB blob warns, does not block" 1 "$RC" "$OUT" "medium.mp4"

# --- 2: oversize deleted in a later unpushed commit is STILL caught --------------
git -C "$R" rm -q big.mp4 medium.mp4; git -C "$R" commit -qm "delete the big files"
run_hook "$R" "$(git -C "$R" rev-parse HEAD)" "$(git -C "$R" rev-parse origin/main)"
check "oversize still in pushed history blocks" 1 "$RC" "$OUT" "big.mp4"

# --- 4: clean range passes silently ---------------------------------------------
C=$(new_repo clean)
echo more > "$C/more.txt"; git -C "$C" add more.txt; git -C "$C" commit -qm more
run_hook "$C" "$(git -C "$C" rev-parse HEAD)" "$(git -C "$C" rev-parse origin/main)"
check "clean range passes" 0 "$RC"
[ -z "$OUT" ] && { echo "ok: clean range is silent"; pass=$((pass+1)); } \
              || { echo "FAIL: clean range printed: $OUT"; fail=$((fail+1)); }

# --- 5: brand-new branch (remote sha is all zeros) -------------------------------
git -C "$C" checkout -q -b feature
echo f > "$C/f.txt"; git -C "$C" add f.txt; git -C "$C" commit -qm feat
OUT=$( (cd "$C" && echo "refs/heads/feature $(git -C "$C" rev-parse HEAD) refs/heads/feature $ZERO" \
        | bash "$HOOK" origin fake-url) 2>&1 ); RC=$?
check "new branch passes" 0 "$RC"

# --- 6: ref deletion (local sha is all zeros) is skipped -------------------------
OUT=$( (cd "$C" && echo "(delete) $ZERO refs/heads/feature $(git -C "$C" rev-parse HEAD)" \
        | bash "$HOOK" origin fake-url) 2>&1 ); RC=$?
check "ref deletion skipped" 0 "$RC"

# --- 7: escape hatch -------------------------------------------------------------
OUT=$( (cd "$R" && echo "refs/heads/main $(git -C "$R" rev-parse HEAD) refs/heads/main $(git -C "$R" rev-parse origin/main)" \
        | SKIP_SIZE_CHECK=1 bash "$HOOK" origin fake-url) 2>&1 ); RC=$?
check "SKIP_SIZE_CHECK=1 bypasses" 0 "$RC" "$OUT" "skipped"

# --- 8-11: the GRADING GATE wiring (2026-09-25) ----------------------------------
# The hook gained a second, independent job: running tests/grading_gate.sh. What is under test here is
# the WIRING, not the gate's own checks (those are the decoder self-test, validate_keys and the
# per-scenario answer tests, which have their own failure modes) — so the gate is STUBBED. The
# throwaway repos above carry no such file, which is exactly why every case before this one still
# passes: a repo without the gate skips it.
G=$(new_repo gated)
mkdir -p "$G/tests"
stub_gate() {  # stub_gate <exit code>
    printf '#!/usr/bin/env bash\nif [ "${SKIP_GRADING_GATE:-}" = "1" ]; then echo "gate skipped"; exit 0; fi\necho "GRADING GATE FAILED: stub"\nexit %s\n' "$1" > "$G/tests/grading_gate.sh"
}
echo x > "$G/x.txt"; git -C "$G" add -A; git -C "$G" commit -qm gate

stub_gate 1
run_hook "$G" "$(git -C "$G" rev-parse HEAD)" "$(git -C "$G" rev-parse origin/main)"
check "a failing grading gate blocks the push" 1 "$RC" "$OUT" "grading gate failed"
check "...and points at the bypass"            1 "$RC" "$OUT" "SKIP_GRADING_GATE=1"

stub_gate 0
run_hook "$G" "$(git -C "$G" rev-parse HEAD)" "$(git -C "$G" rev-parse origin/main)"
check "a passing grading gate lets the push through" 0 "$RC"

# SKIP_SIZE_CHECK used to `exit 0` for the WHOLE hook. Now the two jobs are independent, so bypassing
# the size check must NOT also bypass grading — that is the regression this pins.
stub_gate 1
OUT=$( (cd "$G" && echo "refs/heads/main $(git -C "$G" rev-parse HEAD) refs/heads/main $(git -C "$G" rev-parse origin/main)" \
        | SKIP_SIZE_CHECK=1 bash "$HOOK" origin fake-url) 2>&1 ); RC=$?
check "SKIP_SIZE_CHECK does NOT bypass the grading gate" 1 "$RC" "$OUT" "grading gate failed"

OUT=$( (cd "$G" && echo "refs/heads/main $(git -C "$G" rev-parse HEAD) refs/heads/main $(git -C "$G" rev-parse origin/main)" \
        | SKIP_GRADING_GATE=1 bash "$HOOK" origin fake-url) 2>&1 ); RC=$?
check "SKIP_GRADING_GATE=1 bypasses the gate" 0 "$RC"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
