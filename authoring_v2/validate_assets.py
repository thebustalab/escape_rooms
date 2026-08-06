#!/usr/bin/env python3
"""
validate_assets.py — scenario-wide ASSET completeness + integrity check for the escape rooms.

The audit / wiring skills used to check media only loosely, so a scenario could ship SILENT on every solve
(hawaii shipped with zero `solveSfx`, 2026-07-29) or point a built room at a scene image that isn't on disk
and nothing flagged it. This is the deterministic pass that closes both gaps — the sibling of
`decoder/validate_keys.py`. (Was `validate_sounds.py`; extended to images 2026-07-29.)

Per rooms/<chapter>/<scenario>/scenario.json, for every BUILT room:

  AUDIO
  - MISS  a built room has no ambience `sfx`
  - MISS  a graded gate (`puzzle` or escape `lock`) has no `solveSfx`
  - FAIL  a referenced audio file (`music`, room `sfx[].src`, gate `solveSfx`) is missing on disk

  IMAGES
  - MISS  a built room has no `panorama`; a `ready` scenario has no `cover`
  - FAIL  a referenced image file (`cover`, room `panorama`/`panoramaOpen`, clue `image`,
          `map.image`, `mapview.images[*]`) is missing on disk

  DOORS (topology — the scriptable half of the scene-validator's bidirectional-passage check)
  - MISS  a one-way passage: a forward/open door A->B with no return door back to A in B (or a door
          targeting a missing/unbuilt room). The ART half (inverse geometry both ends) stays an eyeball check.

  CONTENT / TESTS (per scenario — generic conventions, promoted from the per-scenario tests 2026-07-29)
  - MISS  a clue hotspot renders blank — no body, no committed image, no pickup (opens an empty modal)
  - MISS  a graded engine (question/check/pick/map) hands the answer away via feedback.reveal
  - MISS  an MCQ has fewer than 6 options (need >=6 data-derived distractors)
  - MISS  a `ready` scenario has no test_<name>.py (pins each room's answer to the CSV + decoder lockstep)

  GLOBAL (whole repo — only on a full run, not a single-scenario check)
  - STALE   rooms/scenario_inventory.json is out of date (re-run authoring/scenario_inventory.py)
  - IDDUPE  two scenarios share a codec `id` — their submission codes would decode into each other

FAIL = a broken reference (hard bug). MISS = a completeness gap. Status-aware, matching the audit's
promotion gate: a **`status:"ready"` scenario must be perfect** — any FAIL or MISS gates (non-zero exit).
An **`in_development` scenario is a work in progress** — its issues print loudly (`fail (in-dev)` /
`miss (in-dev)`) but never affect the exit code, so building a scenario never turns the check red until you
try to ship it. Referenced paths are checked with any `?v=` cache-buster / `#frag` stripped first.

Usage: validate_assets.py [chapter/scenario ...]   (no args = every scenario)
"""
import json, os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOMS = os.path.join(HERE, "..", "rooms")

def audio_refs(scen):
    if scen.get("music"):
        yield ("music", scen["music"])
    for r in scen.get("rooms", []):
        if not r.get("built"):
            continue
        sfx = r.get("sfx") or []
        if isinstance(sfx, dict):
            sfx = [sfx]
        for x in sfx:
            if x and x.get("src"):
                yield (f"{r['key']} ambience", x["src"])
        for h in r.get("hotspots", []):
            ss = h.get("solveSfx")
            src = ss if isinstance(ss, str) else (ss.get("src") if isinstance(ss, dict) else None)
            if src:
                yield (f"{r['key']}/{h.get('id')} solveSfx", src)

def image_refs(scen):
    if scen.get("cover"):
        yield ("cover", scen["cover"])
    for r in scen.get("rooms", []):
        if not r.get("built"):
            continue
        for f in ("panorama", "panoramaOpen"):
            if r.get(f):
                yield (f"{r['key']} {f}", r[f])
        for h in r.get("hotspots", []):
            if h.get("image"):
                yield (f"{r['key']}/{h.get('id')} clue image", h["image"])
            mp = h.get("map")
            if isinstance(mp, dict) and mp.get("image"):
                yield (f"{r['key']}/{h.get('id')} map.image", mp["image"])
            mv = h.get("mapview")
            if isinstance(mv, dict):
                for st, p in (mv.get("images") or {}).items():
                    if p:
                        yield (f"{r['key']}/{h.get('id')} mapview[{st}]", p)

def door_reciprocity(scen):
    """The scriptable half of the scene-validator's bidirectional-passage check: a door A->B (forward or an
    'open' maze passage with an explicit target) should have a RETURN door in B, so a room can't be entered
    with no way to walk back. Terminal doors (`to:null` — the escape/finish exit) are skipped. Returns a list
    of one-way-passage / bad-target warnings (the *art* half — inverse geometry — stays an eyeball check)."""
    rooms = {r["key"]: r for r in scen.get("rooms", [])}
    out = []
    for r in scen.get("rooms", []):
        if not r.get("built"):
            continue
        for h in r.get("hotspots", []):
            if h.get("type") != "door" or h.get("direction") == "back":
                continue                                  # back doors ARE the return side, not an origin
            to = h.get("to")
            if to is None:
                continue                                  # terminal / escape-exit door — no reciprocal expected
            tgt = rooms.get(to)
            if tgt is None or not tgt.get("built"):
                out.append(f"door '{r['key']}'->'{to}' targets a missing/unbuilt room")
                continue
            tdoors = [x for x in tgt.get("hotspots", []) if x.get("type") == "door"]
            # A door's effective targets = its base `to` PLUS every state-variant `to` (a monorail SWITCH-DOOR
            # routes back OR forward by lever state — its back variant IS the return, even though the base `to`
            # points onward). Without this a switch-door reads as one-way (false positive, 2026-08-05).
            def _door_targets(x):
                ts = {x.get("to")}
                ts.update(v.get("to") for v in (x.get("variants") or []) if v.get("to"))
                return ts
            has_return = any(r["key"] in _door_targets(x) for x in tdoors) or \
                         any(x.get("direction") in ("back", "open") and not x.get("to") and not x.get("variants") for x in tdoors)
            if not has_return:
                out.append(f"one-way passage: '{r['key']}'->'{to}' has no return door back to '{r['key']}' in '{to}'")
    return out

def check_scenario(path):
    d = os.path.dirname(path)
    scen = json.load(open(path, encoding="utf-8"))
    fails, misses = [], []
    ready = scen.get("status") == "ready"
    # completeness (MISS)
    for r in scen.get("rooms", []):
        if not r.get("built"):
            continue
        sfx = r.get("sfx") or []
        if isinstance(sfx, dict):
            sfx = [sfx]
        if not [x for x in sfx if x and x.get("src")]:
            misses.append(f"room '{r['key']}' has no ambience sfx")
        if not r.get("panorama"):
            misses.append(f"room '{r['key']}' (built) has no panorama image")
        for h in r.get("hotspots", []):
            if h.get("type") in ("puzzle", "lock") and not h.get("solveSfx"):
                misses.append(f"gate '{r['key']}/{h.get('id')}' ({h.get('type')}) has no solveSfx")
            # a clue with no body, no committed image, and no pickup opens an EMPTY modal (imagePrompt
            # alone doesn't render — the image must be generated). This shipped blank modals before.
            if h.get("type") == "clue" and not (h.get("body", "") or "").strip() \
               and not h.get("image") and not h.get("pickup"):
                extra = " (imagePrompt set but no committed image)" if h.get("imagePrompt") else ""
                misses.append(f"clue '{r['key']}/{h.get('id')}' renders blank — no body, image, or pickup{extra}")
            # GENERIC content conventions (all scenarios, promoted from the per-scenario tests 2026-07-29):
            # no graded engine may hand the answer away via feedback.reveal, and every MCQ needs >=6 options.
            for eng in ("question", "check", "pick", "map"):
                e = h.get(eng)
                if isinstance(e, dict) and (e.get("feedback", {}) or {}).get("reveal"):
                    misses.append(f"{eng} '{r['key']}/{h.get('id')}' hands the answer away via feedback.reveal (blank it)")
            q = h.get("question")
            if isinstance(q, dict) and len(q.get("options", [])) < 6:
                misses.append(f"MCQ '{r['key']}/{h.get('id')}' has {len(q.get('options', []))} options (need >=6 data-derived)")
    if ready and not scen.get("cover"):
        misses.append("ready scenario has no cover image")
    # every ready scenario must carry a test_<name>.py (pins each room's answer to the CSV + decoder lockstep)
    if ready and not glob.glob(os.path.join(d, "test_*.py")):
        misses.append("no test_<name>.py (pins answers to the CSV + decoder lockstep — a ready scenario needs one)")
    misses.extend(door_reciprocity(scen))                # topology: every passage has a return door
    # integrity (FAIL) — every referenced file must exist. Strip a ?v= cache-buster / #frag first: some
    # refs carry one (e.g. alaska's clue images "escape_grids/mask_room1.png?v=4") — the file on disk has
    # no query, the browser strips it, so must we.
    for label, rel in list(audio_refs(scen)) + list(image_refs(scen)):
        fp = rel.split("?")[0].split("#")[0]
        if not os.path.isfile(os.path.join(d, fp)):
            fails.append(f"{label}: missing file '{rel}'")
    return fails, misses, ready

def main():
    want = sys.argv[1:]
    any_bad = False
    for p in sorted(glob.glob(os.path.join(ROOMS, "*", "*", "scenario.json"))):
        rel = os.path.relpath(p, ROOMS).replace(os.sep + "scenario.json", "")
        if want and rel not in want:
            continue
        fails, misses, ready = check_scenario(p)
        if not fails and not misses:
            print(f"PASS  {rel}" + ("" if ready else "  (in-dev)"))
            continue
        # A `ready` scenario must be perfect (any fail/miss gates); an in_development one is a work in
        # progress — its issues print loudly but don't fail the run (the audit gates it at promotion time).
        if ready:
            for f in fails:  print(f"FAIL  {rel}: {f}")
            for m in misses: print(f"MISS  {rel}: {m}")
            any_bad = True
        else:
            for f in fails:  print(f"fail (in-dev)  {rel}: {f}")
            for m in misses: print(f"miss (in-dev)  {rel}: {m}")
    # global: rooms/scenario_inventory.json must be FRESH (else id/status/has_escape drift) and have NO
    # duplicate codec ids (a collision makes two scenarios' submission codes decode into each other).
    if not want:                                          # only on a full run, not a single-scenario check
        try:
            import scenario_inventory as si
            expected, dupes = si.build_inventory()
            invp = os.path.join(ROOMS, "scenario_inventory.json")
            # round-trip `expected` through JSON so the comparison matches the on-disk file's types
            # (dict int keys — e.g. duplicate_ids {10:…} — become strings once written, so a raw dict
            # compare would always mismatch when there are dupes).
            expected_norm = json.loads(json.dumps(expected))
            if not os.path.isfile(invp) or json.load(open(invp, encoding="utf-8")) != expected_norm:
                print("STALE  scenario_inventory.json out of date — run: python3 authoring/scenario_inventory.py")
                any_bad = True
            if dupes:
                print(f"IDDUPE scenario_inventory: duplicate codec ids {dupes} — give one a fresh id (see next_free_id)")
                any_bad = True
        except Exception as e:
            print(f"(inventory check skipped: {e})")
    sys.exit(1 if any_bad else 0)

if __name__ == "__main__":
    main()
