#!/usr/bin/env python3
"""test_temple.py — regression guards for hierarchical_clustering/temple.

The graded rungs are re-derived from the CSV by `_scratch/verify_temple_data.R`, and the escape's
grouping is brute-forced by `_scratch/verify_temple_escape.py`. This file guards the seam between those
two and the SHIPPED scenario — the places where a correct answer and a correct board can still ship a
broken room. Run: python3 test_temple.py   (stdlib + the two scratch modules.)

Failure modes it guards:
  - a niche clue loses its FIGURE PLATE, or points at a plate that isn't on disk. This is the one that
    would silently kill the escape: after the 2026-08-27 lamp-hall probe the scene art is explicitly NOT
    required to make the figures identifiable (gpt-image rendered the bee as a pot and the monkey as a
    cat), so the deterministic plate is now the ONLY carrier of the evidence. No plate, no escape.
  - a plate drifts from the verified board — the image says one set of figures, the file that proves the
    grouping is unique says another;
  - the NAMELESS niche (the walled-up tenth shrine) gains figures or a plate. It must have neither: with
    no figures it cannot be placed in the Register of the Gods, which is the whole point of it;
  - the ledger's authored groups stop matching the verified 2/3/4 partition;
  - a banner colour is reused, or a niche's colour stops matching its plate — the colour IS the ledger's
    row identifier, so a collision makes two rows indistinguishable;
  - the escape's `when` stops matching the key its dial sets, so the payoff art never fires.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(cond, msg):
    print(("  ok  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    esc = _load("_t_escape", "_scratch/verify_temple_escape.py")
    scn = _load("_t_scenario", "_scratch/build_scenario.py")
    doc = json.load(open(os.path.join(HERE, "scenario.json"), encoding="utf-8"))
    planned = {h.get("label"): (r["key"], h)
               for r in doc["rooms"] for h in (r.get("plannedHotspots") or [])}

    print("== figure plates: the escape's only evidence ==")
    for shrine, figs in sorted(esc.STATUES.items()):
        colour, _ = scn.NICHE[shrine]
        label = "The %s niche" % colour
        check(label in planned, "%s has a niche clue labelled %r" % (shrine, label))
        if label not in planned:
            continue
        _room, h = planned[label]
        img = h.get("image")
        check(img == "figures/%s.png" % shrine.lower(),
              "%s's clue carries its own plate (got %r)" % (shrine, img))
        check(bool(img) and os.path.isfile(os.path.join(HERE, img)),
              "%s's plate exists on disk" % shrine)

    print("== plates agree with the VERIFIED board ==")
    # re-render nothing; just confirm make_figures reads the same board this test does
    figmod = _load("_t_figures", "make_figures.py")
    check(figmod.STATUES == esc.STATUES,
          "make_figures draws from verify_temple_escape's board, not a copy of it")
    check(set(figmod.GLYPH) == set(figmod.ORDER), "every glyph is in the draw order")
    drawn = set().union(*esc.STATUES.values())
    check(drawn == set(figmod.ORDER),
          "every figure type is used by some shrine (no dead glyphs): %s" % sorted(set(figmod.ORDER) - drawn))

    print("== the nameless niche stays out of the register ==")
    nameless = planned.get("The nameless niche")
    check(nameless is not None, "the sealed cell has its nameless niche")
    if nameless:
        check(not nameless[1].get("image"),
              "it carries NO figure plate — with no figures it cannot be placed in the Register")

    print("== banner colours are the ledger's row identifiers ==")
    colours = [c for c, _f in scn.NICHE.values()]
    check(len(set(colours)) == 9, "all nine banner colours are distinct (got %d)" % len(set(colours)))
    for shrine in esc.STATUES:
        colour, _ = scn.NICHE[shrine]
        check(colour in figmod._BANNER_HEX, "%s's colour %r has a plate hex" % (shrine, colour))
    # and the colours must not encode the grouping, or the escape is free
    for god, members in esc.INTENDED.items():
        cols = {scn.NICHE[s][0] for s in members}
        check(len(cols) == len(members), "%s's shrines do not share a banner colour" % god)

    print("== the ledger's authored groups match the verified partition ==")
    led = planned.get("The Register of the Gods")
    check(led is not None, "the altar carries the ledger")
    if led:
        note = led[1].get("note", "")
        for god, members in esc.INTENDED.items():
            cols = sorted(scn.NICHE[s][0] for s in members)
            got = re.search(r"%s \{([^}]*)\}" % god, note)
            check(got is not None, "the ledger note names the %s group" % god)
            if got:
                check(sorted(x.strip() for x in got.group(1).split(",")) == cols,
                      "%s = %s in the note" % (god, ", ".join(cols)))

    print("== the payoff variant fires on the key the dial sets ==")
    altar = next(r for r in doc["rooms"] if r["key"] == "sun_altar")
    els = {e["id"]: e for e in altar["authoring"]["sceneSpec"]["elements"]}
    dial_key = els["flame_dial"].get("key")
    var = (els["basin_ring"].get("variants") or [{}])[0]
    check(dial_key == "temple_fires", "the flame dial sets `temple_fires` (got %r)" % dial_key)
    check(var.get("when") == {"eq": [dial_key, "lit"]},
          "the lit-ring variant fires on that same key (got %r)" % (var.get("when"),))
    check(bool(var.get("reveal")), "the lit-ring variant has a reveal, so its art gets queued")

    print("\n" + ("all checks passed" if not fails else "FAILURES ABOVE"))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
