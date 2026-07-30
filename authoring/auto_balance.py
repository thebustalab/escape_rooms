#!/usr/bin/env python3
"""auto_balance.py — perceived-loudness (EBU R128 / LUFS) sfx auto-balance for an escape-room scenario.

Lowers every sound effect — each room's `sfx` layers and every solve/door `solveSfx` sting — so none
PLAYS louder than the background music at its authored volume. Perceived loudness (LUFS, RMS fallback
for very short stings), measured with ffmpeg; reduce-only (a quiet effect is left alone). Run this as
the LAST sfx step: after the music is finalised and every room's sfx + solve stings are wired, right
before the audit. Then fine-tune by ear in the test-play sound mixer (▶ Test play).

    python3 auto_balance.py <chapter> <scenario>            # measure + apply + write scenario.json
    python3 auto_balance.py <chapter> <scenario> --dry-run  # report only, write nothing

Shares one implementation with the harness's /api/auto-balance endpoint (harness_server._apply_balance),
so the agent's wire-time pass and the mixer's Auto-balance button always compute the same volumes.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_server as hs   # safe: server only starts under its own __main__ guard


def main(argv):
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    chapter, scenario = args
    try:
        base = hs._scenario_base(chapter, scenario)
    except ValueError as e:
        print("✗", e)
        return 1

    res = hs._apply_balance(base, apply=not dry)
    if res.get("error"):
        print("✗", res["error"])
        return 1

    print("music: %s  %s %s  @ volume %s"
          % (res.get("music"), res.get("musicLoudness"), res.get("musicMetric"), res.get("musicVolume")))
    changes = res.get("changes", [])
    verb = "would lower" if dry else "lowered"
    if not changes:
        print("nothing to lower — every effect already sits under the music.")
    for c in changes:
        where = c.get("room") or "scenario"
        print("  %s%-5s %-16s %-44s %s %s : %s -> %s"
              % ("(dry) " if dry else "", c["kind"], where, c["src"],
                 c["loudness"], c["metric"], c["oldVolume"], c["newVolume"]))
    for s in res.get("skipped", []):
        print("  skip  %-16s %-44s (%s)" % (s.get("room") or "scenario", s["src"], s["reason"]))
    print("%s %d effect(s); %d skipped (unmeasurable)." % (verb, len(changes), len(res.get("skipped", []))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
