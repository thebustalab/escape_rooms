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
            has_return = any(x.get("to") == r["key"] for x in tdoors) or \
                         any(x.get("direction") in ("back", "open") and not x.get("to") for x in tdoors)
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
    if ready and not scen.get("cover"):
        misses.append("ready scenario has no cover image")
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
    sys.exit(1 if any_bad else 0)

if __name__ == "__main__":
    main()
