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
  - MISS  a graded gate (`puzzle`/`lock`/`grid`/`ledger`) has no `solveSfx`
  - MISS  a `clue` renders a BLANK modal (no body, no committed image, no pickup CAPTION —
          note `pickup:true` is not a caption)
  - VBUMP shared-engine `?v=` cache tokens drift, or pano-player.js has a bare local import
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
  - MISS  a `dial` with no `states` — the card renders a gauge and NO buttons, so the control is inert and
          falls back to the generic hint. temple's flame dial and all five of spa's bell-cords shipped this
          way (2026-08-27); the temple one was the scenario's whole finale.
  - MISS  a PICKUP clue's image is not square — the field notebook's collage board paints each tile as a
          120px square with `object-fit:cover`, so a wide image is CENTRE-CROPPED and the edges of the
          evidence never reach the board (temple's 900x360 figure plates showed their middle figure only,
          2026-08-27). Square art is the convention every other set already follows.
  - MISS  a graded engine (question/check/pick/map) hands the answer away via feedback.reveal
  - MISS  an MCQ has fewer than 6 options (need >=6 data-derived distractors)
  - MISS  a `ready` scenario has no test_<name>.py (pins each room's answer to the CSV + decoder lockstep)
  - MISS  `done`/`escapeDone`/`debrief` is a bare string rather than an object — the engine reads
          `.title`/`.body`, so the authored finish screen silently falls back to the generic one
          (subway + clouds, found 2026-09-07). Valid JSON, clean prose, screen still renders: nothing
          else catches this.
  - MISS  `status` is neither "in_development" nor "ready" — a free-text progress note in the promotion
          SWITCH reads as not-ready by accident and lands verbatim in scenario_inventory.json (subway
          carried a 641-char build report there; clouds/heist/beacons too, 2026-09-07). Notes belong in
          `_designNotes.buildState`.

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
import json, os, struct, sys, glob

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

def _png_jpeg_size(path):
    """(w, h) for a PNG or JPEG, header-only — no Pillow on this box, and none is needed. Returns None
    for anything it can't read, so an exotic format is skipped rather than mis-flagged."""
    try:
        with open(path, "rb") as f:
            head = f.read(2)
            if head == b"\xff\xd8":                       # JPEG: walk the segment chain to a SOFn
                while True:
                    b = f.read(1)
                    if not b:
                        return None
                    if b != b"\xff":
                        continue
                    marker = f.read(1)
                    while marker == b"\xff":
                        marker = f.read(1)
                    if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3"):
                        f.read(3)
                        h, w = struct.unpack(">HH", f.read(4))
                        return (w, h)
                    ln = struct.unpack(">H", f.read(2))[0]
                    f.seek(ln - 2, 1)
            f.seek(0)
            sig = f.read(24)
            if sig[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", sig[16:24])
    except Exception:
        return None
    return None


# A pickup clue's image lands on the notebook's collage BOARD, whose tiles are square and cropped with
# `object-fit:cover` — so anything much wider or taller than square loses its edges exactly where the
# player is meant to compare the whole set. 1.25 is deliberately loose: it passes a plate that is a little
# off-square and catches the strip/banner shapes that actually hide content.
SQUARE_TOL = 1.25


def pickup_tile_shape(scen, d):
    out = []
    for r in scen.get("rooms", []):
        for h in (r.get("hotspots") or []):
            if not isinstance(h, dict) or not h.get("pickup") or not h.get("image"):
                continue
            fp = h["image"].split("?")[0].split("#")[0]
            size = _png_jpeg_size(os.path.join(d, fp))
            if not size or not size[1]:
                continue
            ar = size[0] / size[1]
            if ar > SQUARE_TOL or ar < 1 / SQUARE_TOL:
                out.append("pickup clue '%s/%s' image is %dx%d (%.2f:1) — the notebook board crops tiles "
                           "SQUARE, so this loses its edges on the board; author pickup art square"
                           % (r["key"], h.get("id"), size[0], size[1], ar))
    return out


def dials_without_states(scen):
    """A `dial` writes a world-state key by clicking one of its `states`. With no states there is nothing to
    click: the modal shows a decorative gauge, no buttons, and the engine's generic fallback hint — an inert
    control the player can't tell from a bug."""
    out = []
    for r in scen.get("rooms", []):
        for h in (r.get("hotspots") or []):
            if isinstance(h, dict) and h.get("type") == "dial" and not (h.get("states") or []):
                out.append("dial '%s/%s' has no `states` — nothing to click, so it is inert"
                           % (r["key"], h.get("id")))
    return out


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

def clip_state_pairing(scen):
    """Full-scene STATES whose motion does not match their backdrop. Returns (misses, fails).

    A baked clip has its source still BAKED INTO IT — the motion mask means every static pixel shows the
    image the clip was generated from. So a full-scene variant (box [0,0,1,1]) replaces the backdrop the
    clip was made from, and the engine's rule (`variant_resolve.pickCinemagraphs`) is that a clip only
    plays while the image it came from is the one showing. Two ways that goes wrong, and NEITHER is
    visible in any other check:

      * a full-scene state with NO clip tagged for it — the room goes completely STATIC in that state.
        Egypt has seven night backdrops and no night clips, so the whole world freezes after dark.
      * a clip tagged for a state no variant declares — ORPHANED, it will never play at all.

    Boxed variants are deliberately not checked: they change a region, not the backdrop, so the base
    clips keep playing over them and no per-state clip is owed. That is the cheap route, and the whole
    reason a scenario should prefer boxed variants when it can.
    """
    misses, fails = [], []
    for r in scen.get("rooms", []):
        if not r.get("built"):
            continue
        hs = r.get("hotspots") or []
        full = lambda b: isinstance(b, list) and b == [0, 0, 1, 1]
        # declared full-scene variant states on this room
        states = set()
        for h in hs:
            for v in (h.get("variants") or []):
                if v.get("panorama") and full(v.get("box") if isinstance(v.get("box"), list) else h.get("box")):
                    states.add(v.get("state"))
        clips = [h["cinemagraph"] for h in hs if isinstance(h.get("cinemagraph"), dict) and h["cinemagraph"].get("video")]
        has_full_base = any(full(c.get("box")) and not c.get("state") for c in clips)
        clip_states = {c.get("state") for c in clips if c.get("state")}
        for st in sorted(x for x in states if x):
            if st not in clip_states and clips:
                misses.append(f"room '{r['key']}' state '{st}' is a full-scene backdrop with NO clip tagged "
                              f"for it — every clip stops in that state and the room goes static"
                              + (" (its base clip is full-scene, so it cannot carry over)" if has_full_base else ""))
        for st in sorted(clip_states - states):
            fails.append(f"room '{r['key']}' clip is tagged state '{st}' but no full-scene variant declares "
                         f"that state — it can never play")
    return misses, fails


def check_scenario(path):
    d = os.path.dirname(path)
    scen = json.load(open(path, encoding="utf-8"))
    fails, misses = [], []
    ready = scen.get("status") == "ready"

    # `status` IS THE PROMOTION SWITCH, and its vocabulary is closed: "in_development" or "ready"
    # (absent = in_development). It is not a free-text progress note. The generator surfaces it into
    # rooms/scenario_inventory.json and downstream surfaces filter on == "ready" (the newsletter's
    # test-drive dropdown, newsletter/newsletter.py), so a prose value behaves as not-ready by
    # accident rather than by decision, and dumps a paragraph into the inventory on the way past.
    # Found 2026-09-07 auditing subway, which carried a 641-character build report here; clouds,
    # heist and beacons had done the same thing. Checked centrally rather than fixed four times,
    # per the audit's "a new generic error class belongs in the validator" rule. The progress note
    # is worth keeping — put it in `_designNotes.buildState`, which is where subway's went.
    if scen.get("status") is not None and scen["status"] not in ("in_development", "ready"):
        misses.append("`status` is prose, not the in_development/ready SWITCH the inventory and the "
                      "newsletter dropdown read — move the note to `_designNotes.buildState` "
                      f"(got {scen['status'][:60]!r}...)")

    # `done` / `escapeDone` / `debrief` must be OBJECTS, not bare strings. The engine reads
    # `SCENARIO.done.title` and `SCENARIO.done.body` (pano-player.js -> finishAnalysis / showEscapeDone);
    # a string has no `.title`, so BOTH fall through to the generic "Nice work — you've finished this
    # scenario." and the authored finish screen is never once shown to a player. Nothing caught it:
    # the JSON is valid, the text passes validate_story.py, and the screen still renders. Found
    # 2026-09-07 in subway, whose two lines were the intended TITLES; clouds has the same shape.
    for fld in ("done", "escapeDone", "debrief"):
        v = scen.get(fld)
        if v is not None and not isinstance(v, dict):
            misses.append(f"`{fld}` is a bare {type(v).__name__}, not an object — the engine reads "
                          f"`{fld}.title`/`.body`, so the authored screen never shows and the player "
                          f"gets the generic fallback. Wrap it: {{\"title\": ..., \"body\": ...}}")

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
            # ALL FOUR gate types, matching pano-player's `gates` filter — a ledger or grid escape is
            # as much a solve as a puzzle. The narrower ("puzzle","lock") test silently stopped applying
            # to temple's sun_altar the moment its escape was corrected from `puzzle` to its real
            # `ledger` type (2026-08-28): the room went from flagged to clean without gaining a sound.
            if h.get("type") in ("puzzle", "lock", "grid", "ledger") and not h.get("solveSfx"):
                misses.append(f"gate '{r['key']}/{h.get('id')}' ({h.get('type')}) has no solveSfx")
            # a clue with no body, no committed image, and no pickup CAPTION opens an EMPTY modal
            # (imagePrompt alone doesn't render — the image must be generated). This shipped blank modals
            # before. NOTE: only a STRING pickup supplies display content (the notebook caption); a boolean
            # `pickup:true` with an empty body + no image still renders a blank modal AND logs a contentless
            # notebook entry (this shipped in hospital's Editor's note B — pickup:true masked the empty body).
            pickup = h.get("pickup")
            pickup_caption = pickup.strip() if isinstance(pickup, str) else ""
            if h.get("type") == "clue" and not (h.get("body", "") or "").strip() \
               and not h.get("image") and not pickup_caption:
                extra = " (imagePrompt set but no committed image)" if h.get("imagePrompt") else ""
                if pickup is True:
                    extra += " (pickup:true but empty body + no image → blank modal, contentless notebook entry)"
                misses.append(f"clue '{r['key']}/{h.get('id')}' renders blank — no body, image, or pickup caption{extra}")
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
    misses.extend(dials_without_states(scen))            # a stateless dial is an inert control
    misses.extend(pickup_tile_shape(scen, d))            # notebook board tiles are square-cropped
    _cm, _cf = clip_state_pairing(scen)                  # a full-scene state whose motion doesn't match it
    misses.extend(_cm); fails.extend(_cf)
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

        # global: shared-engine cache tokens must be COHERENT. `pano-player.js` imports its local helper
        # modules with a ?v= token; that token AND the ?v= on every play.html's <script src=pano-player.js>
        # must all match. A drift leaves browsers on a STALE cached helper module → a "doesn't provide an
        # export named X" SyntaxError → blank page. Also flags a BARE local import (never cache-busted).
        # (The 2026-08-05 airship regression: a bumped pano-player.js imported variant_resolve.js bare, so
        # browsers kept the pre-`activeDoorVariant` copy and the whole engine module failed to parse.)
        # Ported from the retired v1 copy 2026-08-29 — it was the only place this check lived, and that
        # copy is now unrunnable under `z_authoring_v1/` (its relative ROOMS path no longer resolves).
        try:
            import re as _re
            shared = os.path.join(HERE, "..", "shared")
            # Scan EVERY module in shared/, not just pano-player.js (widened 2026-09-04). A helper that
            # imports another helper is the same stale-module trap one level down, and the old
            # pano-player-only scan could not see it: webr-console.js -> webr_view.js was invisible.
            imp_tokens, bare_imports = set(), []
            for mod in sorted(glob.glob(os.path.join(shared, "*.js"))):
                src = open(mod, encoding="utf-8").read()
                imp_tokens |= set(_re.findall(r'from\s+"\./[\w-]+\.js\?v=(\d+)"', src))
                bare_imports += [(os.path.basename(mod), m)
                                 for m in _re.findall(r'from\s+"(\./[\w-]+\.js)"', src)]
            shells = glob.glob(os.path.join(ROOMS, "*", "*", "play.html")) + [os.path.join(shared, "test_play.html")]
            tag_tokens = set()
            for sh in shells:
                tag_tokens |= set(_re.findall(r'pano-player\.js\?v=(\d+)', open(sh, encoding="utf-8").read()))
            if bare_imports:
                for mod, imp in bare_imports:
                    print(f"VBUMP  {mod} imports {imp} with NO ?v= token (a bare local import is never cache-busted — add ?v=N in lockstep with the engine)")
                any_bad = True
            if len(imp_tokens | tag_tokens) > 1:
                print(f"VBUMP  shared-engine cache tokens drift — shared/*.js imports {sorted(imp_tokens)} vs play.html <script> tags {sorted(tag_tokens)}; bump ALL to one ?v=N (stale-helper-module SyntaxError risk)")
                any_bad = True
        except Exception as e:
            print(f"(engine-token check skipped: {e})")
    sys.exit(1 if any_bad else 0)

if __name__ == "__main__":
    main()
