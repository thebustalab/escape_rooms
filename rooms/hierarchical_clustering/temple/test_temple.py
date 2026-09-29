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
import hashlib
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

    print("== the painted figure tiles are the ones we checked ==")
    # WHY A CHECKSUM (2026-09-20). The plates stopped being drawn shapes and became pasted paintings,
    # one file per figure TYPE, shared by every shrine that owns it. That is what makes "the same frog"
    # literally the same pixels. It also means a regenerated tile silently changes the evidence in up to
    # four plates at once, so the bytes are pinned: regenerate deliberately, look at all twelve, and
    # update MANIFEST.json in the same commit.
    tdir = os.path.join(HERE, "figures", "tiles")
    man_path = os.path.join(tdir, "MANIFEST.json")
    check(os.path.isfile(man_path), "the figure tiles carry a checksum manifest")
    if os.path.isfile(man_path):
        man = json.load(open(man_path))["tiles"]
        check(set(man) == set(figmod.ORDER),
              "a tile exists for every figure type: missing %s" % sorted(set(figmod.ORDER) - set(man)))
        for name, want in sorted(man.items()):
            p = os.path.join(tdir, name + ".png")
            if not os.path.isfile(p):
                check(False, "tile %s is on disk" % name)
                continue
            got = hashlib.sha1(open(p, "rb").read()).hexdigest()
            check(got == want,
                  "tile %s matches the manifest (regenerated art? re-check it, then update MANIFEST.json)" % name)

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

    # ---- the ledger's rubric: it must NAME each group without BUILDING any of them ---------------
    # Lucas, playtest 2026-09-28: "I got the cluster correct - easy, but how to ascribe which to its
    # identifier?" The nine figure-plates let you GROUP the banners (a god's shrines share most of their
    # figures and none with another god's), but nothing said WHICH group was the Rain. Fixed with a rubric
    # in the ledger's own prompt naming one emblem per god — deliberately NOT in the art, because the
    # plates already label every figure and re-rendering nine of them for a legend would be absurd.
    #
    # The rubric must stay BALANCED, which is what this pins:
    #   * each named emblem belongs to exactly ONE god (otherwise it misleads), and
    #   * each appears on SOME but NOT ALL of that god's shrines — so it labels a group the player has
    #     already formed and can never assign every shrine by itself.
    # `frog`/`shell` (2/2 of Rain) and `spindle-whorl` (3/3 of Ember) are the tempting picks that WOULD
    # hand over the answer; if the rubric ever drifts onto one, this fails.
    print("\n== the ledger rubric names each group without solving it ==")
    ledger = next(h for r in doc["rooms"] for h in (r.get("hotspots") or [])
                  if h.get("id") == "register_gods")
    prompt = ledger.get("prompt") or ""
    for god, emblem in (("Rain", "rain-jar"), ("Ember", "censer"), ("Canopy", "seed-pod")):
        check(emblem in prompt, "the rubric names the %s's emblem (%s)" % (god, emblem))
        carry = {s for s, figs in esc.STATUES.items() if emblem in figs}
        gods = {g for g, members in esc.INTENDED.items() for s in carry if s in members}
        check(gods == {god}, "%s appears only on %s shrines (%s)"
              % (emblem, god, ", ".join(sorted(carry))))
        check(0 < len(carry) < len(esc.INTENDED[god]),
              "%s covers %d of the %d %s shrines — enough to name the group, not to build it"
              % (emblem, len(carry), len(esc.INTENDED[god]), god))

    check_rungs(doc)

    print("\n" + ("all checks passed" if not fails else "FAILURES ABOVE"))
    return 1 if fails else 0

# ---------------------------------------------------------------------------------------------------
# THE GRADED RUNGS, RE-DERIVED FROM THE CSV (added 2026-09-29).
#
# WHY THIS EXISTS. Until today the only re-derivation of the four answers lived in
# `_scratch/verify_temple_data.R`, which needs Rscript and so was not on the path any gate ran. That is
# how the rung-1 TIE shipped: Longshadow sat exactly midway between Ninestep and Deepwell on
# copal/rubber_latex while Ninestep and Deepwell were identical in the other four columns, so
# d(Ninestep, Longshadow) == d(Longshadow, Deepwell) EXACTLY. "Which shrine joins Ninestep first" was
# then decided by the tie-break order of the distance matrix under EVERY linkage rule and with scaling
# on or off — the rung had no single correct answer, and every test still passed, because every test
# only asked whether the answer was `Longshadow`, which a tie-break happened to deliver.
#
# So this block does not merely check the winners. It checks that each winner wins BY A MARGIN, it
# refuses an exact tie outright, and it pins the DISTANCES QUOTED IN THE PROSE against the CSV, which
# is the other half of what went stale. Pure stdlib (Lance-Williams ward.D2), so it runs anywhere
# `python3 test_temple.py` runs.
# ---------------------------------------------------------------------------------------------------
import csv as _csv
import math as _math


def _read(path):
    with open(os.path.join(HERE, path), newline="", encoding="utf-8") as f:
        rows = list(_csv.DictReader(f))
    cols = ["copal", "rubber_latex", "cacao", "agave", "beeswax", "seed_oil"]
    return [(r["shrine"], r.get("wing"), [float(r[c]) for c in cols]) for r in rows]


def _zscale(rows):
    """Column-wise z-scores, sample SD (n-1) — what R's scale() and scale_variance = TRUE do."""
    n, k = len(rows), len(rows[0][2])
    mu = [sum(r[2][j] for r in rows) / n for j in range(k)]
    sd = [_math.sqrt(sum((r[2][j] - mu[j]) ** 2 for r in rows) / (n - 1)) for j in range(k)]
    return [(s, w, [(v[j] - mu[j]) / sd[j] for j in range(k)]) for s, w, v in rows]


def _dmat(rows):
    return {(a[0], b[0]): _math.dist(a[2], b[2])
            for i, a in enumerate(rows) for b in rows[i + 1:]}


def _ward_d2(rows, k):
    """Agglomerate to k clusters by Ward's D2, via Lance-Williams on un-squared Euclidean distances.
    Same rule as R's hclust(method = "ward.D2") and runMatrixAnalysis(agglomeration_method = 'ward.D2')."""
    groups = {i: [r[0]] for i, r in enumerate(rows)}
    d = {}
    for i, a in enumerate(rows):
        for j, b in enumerate(rows):
            if i < j:
                d[(i, j)] = _math.dist(a[2], b[2])
    nxt = len(rows)
    key = lambda i, j: (min(i, j), max(i, j))
    while len(groups) > k:
        (a, b), _best = min(((p, v) for p, v in d.items()
                             if p[0] in groups and p[1] in groups), key=lambda kv: (kv[1], kv[0]))
        na, nb = len(groups[a]), len(groups[b])
        new = {}
        for c in groups:
            if c in (a, b):
                continue
            nc = len(groups[c])
            dac, dbc, dab = d[key(a, c)], d[key(b, c)], d[key(a, b)]
            new[c] = _math.sqrt(((na + nc) * dac ** 2 + (nb + nc) * dbc ** 2 - nc * dab ** 2)
                                / (na + nb + nc))
        groups[nxt] = groups.pop(a) + groups.pop(b)
        for c, v in new.items():
            d[key(nxt, c)] = v
        nxt += 1
    return [sorted(v) for v in groups.values()]


def check_rungs(doc):
    nine = _read(os.path.join("data", "temple_votive_residues.csv"))
    unk = _read(os.path.join("data", "unknown_shrine.csv"))
    names = [r[0] for r in nine]

    print("\n== rung 1: the first merge must be DATA, not a tie-break ==")
    quoted = {}
    for label, rows in (("unscaled", nine), ("scaled", _zscale(nine))):
        d = _dmat(rows)
        ranked = sorted(d.items(), key=lambda kv: kv[1])
        (pair, d1), (pair2, d2) = ranked[0], ranked[1]
        check(set(pair) == {"Ninestep", "Longshadow"},
              "%s: the closest pair in the whole table is Ninestep+Longshadow (got %s at %.4f)"
              % (label, " + ".join(sorted(pair)), d1))
        # THE TIE GUARD. A ratio, not an equality test: an exact tie is the disease, but anything
        # inside 25% is close enough that a rounding change or a linkage swap could reorder it.
        check(d2 > d1 * 1.25,
              "%s: no near-tie for the first merge — runner-up pair %s is %.0f%% further (needs >25%%)"
              % (label, " + ".join(sorted(pair2)), 100 * (d2 / d1 - 1)))
        nl = d[("Ninestep", "Longshadow")]
        ld = d[("Longshadow", "Deepwell")]
        check(abs(nl - ld) > 1e-9,
              "%s: Longshadow is NOT equidistant from Ninestep and Deepwell (%.4f vs %.4f) — "
              "the 2026-09-29 tie defect has not returned" % (label, nl, ld))
        # and the rung as the player meets it: nearest shrine TO NINESTEP, with its runner-up
        frm = sorted(((d[tuple(sorted((n, "Ninestep"), key=names.index))], n)
                      for n in names if n != "Ninestep"))
        check(frm[0][1] == "Longshadow",
              "%s: nearest shrine to Ninestep is Longshadow (got %s, d=%.4f)" % (label, frm[0][1], frm[0][0]))
        check(frm[1][0] > frm[0][0] * 1.25,
              "%s: single winner — runner-up %s is %.0f%% further" % (label, frm[1][1], 100 * (frm[1][0] / frm[0][0] - 1)))
        if label == "unscaled":
            quoted = {"d1": frm[0][0], "runner": frm[1][1], "d2": frm[1][0]}

    print("\n== the rung-1 prose quotes the CSV's real numbers ==")
    pick = next(h["pick"] for r in doc["rooms"] for h in (r.get("hotspots") or []) if h.get("id") == "table_sun")
    corr = pick["feedback"]["correct"]
    check("%.1f apart" % quoted["d1"] in corr,
          "the correct-feedback quotes %.1f as the Ninestep-Longshadow distance (says: %r)"
          % (quoted["d1"], corr))
    check("next nearest shrine, %s, is %.1f away" % (quoted["runner"], quoted["d2"]) in corr,
          "it names the real runner-up and its real distance (%s, %.1f)" % (quoted["runner"], quoted["d2"]))

    print("\n== rung 1's reference code pins every setting that could move the answer ==")
    code = pick["plotCode"]
    for arg in ('analysis = "hclust"', "scale_variance =", "tree_method =", "agglomeration_method =",
                "columns_w_values_for_single_analyte =", "columns_w_sample_ID_info ="):
        check(arg in code, "plotCode states %s explicitly (no silent default)" % arg)
    check("dist(" not in code and "rownames(" not in code and "as.matrix(" not in code,
          "plotCode uses the taught runMatrixAnalysis route, not base-R dist()/rownames()")

    print("\n== the k=3 cut, and the three check rungs ==")
    fams = {tuple(g): g for g in _ward_d2(nine, 3)}
    got = sorted(fams.values(), key=len)
    check([sorted(g) for g in got] == [["Lastcourt", "Quietfloor"],
                                       ["Highgate", "Palewall", "Redsill"],
                                       ["Brokenarch", "Deepwell", "Longshadow", "Ninestep"]],
          "ward.D2 cut to k=3 gives {drink 2} {balm 3} {smoke 4} — got %s"
          % " | ".join("+".join(g) for g in got))

    bees = {r[0]: r[2][4] for r in nine}
    means = sorted(((sum(bees[s] for s in g) / len(g), sorted(g)) for g in got), reverse=True)
    check(means[0][1] == ["Highgate", "Palewall", "Redsill"],
          "rung 3 (lamp_hall): top-beeswax family is Highgate+Palewall+Redsill — got %s" % means[0][1])
    check(means[0][0] > means[1][0] * 2,
          "rung 3 single winner: %.1f vs %.1f and %.1f" % (means[0][0], means[1][0], means[2][0]))
    lamp = next(h["check"] for r in doc["rooms"] for h in (r.get("hotspots") or []) if h.get("id") == "wax_bench")
    check("%.1f, against %.1f and %.1f" % (means[0][0], means[1][0], means[2][0]) in lamp["feedback"]["correct"],
          "the lamp_hall prose quotes the real means %.1f / %.1f / %.1f (says: %r)"
          % (means[0][0], means[1][0], means[2][0], lamp["feedback"]["correct"]))

    ten = nine + unk
    fam10 = _ward_d2(ten, 3)
    with_unk = sorted(set(next(g for g in fam10 if "Unmarked_Cell" in g)) - {"Unmarked_Cell"})
    check(with_unk == ["Lastcourt", "Quietfloor"],
          "rung 2 (sealed_cell): the Unmarked Cell joins Quietfloor+Lastcourt — got %s" % with_unk)
    d10 = _dmat(ten)
    un = sorted((v, tuple(set(p) - {"Unmarked_Cell"})[0]) for p, v in d10.items() if "Unmarked_Cell" in p)
    check(un[1][0] < 3 and un[2][0] > 55,
          "rung 2 is not a close call: nearest two %s %.2f / %s %.2f, next %s %.2f"
          % (un[0][1], un[0][0], un[1][1], un[1][0], un[2][1], un[2][0]))
    cell = next(h["check"] for r in doc["rooms"] for h in (r.get("hotspots") or []) if h.get("id") == "table_cell")
    txt = cell["feedback"]["correct"] + " " + " ".join(cell["feedback"]["wrong"])
    check("%.1f from each" % un[0][0] in cell["feedback"]["correct"],
          "the sealed_cell prose quotes the real %.1f (says: %r)" % (un[0][0], cell["feedback"]["correct"]))
    check(un[2][0] > 60, "the prose's 'more than 60 from every other shrine' still holds "
                         "(nearest outsider %s is %.2f away)" % (un[2][1], un[2][0]))

    wing = {r[0]: r[1] for r in nine}
    fam_of = {s: i for i, g in enumerate(got) for s in g}
    odd = []
    for w in sorted(set(wing.values())):
        here = [s for s in names if wing[s] == w]
        counts = {}
        for s in here:
            counts[fam_of[s]] = counts.get(fam_of[s], 0) + 1
        dom = max(counts, key=lambda c: counts[c])
        odd += [s for s in here if fam_of[s] != dom]
    check(sorted(odd) == ["Deepwell", "Palewall"],
          "rung 4 (inner_vault): the moved shrines are Deepwell+Palewall — got %s" % sorted(odd))
    check(len(names) - len(odd) == 7,
          "7 of 9 shrines still agree with their wing, so the wing decoy stays tempting")


if __name__ == "__main__":
    raise SystemExit(main())

