#!/usr/bin/env python3
"""Escape v3 (facet-collage) — the 9-postcard Latin square, its digit map, and the code check.

Deterministic, stdlib-only. This is the DESIGN VERIFIER for the hospital escape's combinatorics — the
Phase-2 analogue of "verify every answer against the CSV" for the analysis rooms (this escape is
decoupled from the lake data, so what has to be verified is the *arrangement*, not a dataset value).

It proves the three properties the puzzle relies on:
  1. Every PAIR of the three faceting variables fully crosses (each 3x3 tiling is clean — no empty cell,
     no collision), so whichever two variables the player facets by, the grid always looks complete and
     no arrangement visibly "fails" (that would give the answer away).
  2. The six ordered (rows, cols) pairings yield six DISTINCT 3-digit codes (the middle row, read L->R).
  3. The two editorial notes select exactly ONE pairing (rows = season, cols = remoteness) -> the code.

Run:  python3 escape2_facets.py     (prints the card table + all six codes; asserts the intended one)
"""

# --- three ORDINAL faceting variables, each 3 levels (index = position in the natural order) ----------
SEASON = ["June", "July", "August"]              # A — down the page (rows); middle level = July
REMOTE = ["roadside", "short hike", "backcountry"]  # B — across (cols); left = gentle, right = wild
LENGTH = ["a day", "a weekend", "a week"]        # C — the DECOY dimension (editor rules it out)

# The 9 postcards form a Graeco-Latin square: index each card by (a, b) and set the third variable
# c = (a + b) % 3. That makes ALL THREE pairwise crossings complete (property 1).
def length_index(a, b):
    return (a + b) % 3

# --- digit printed prominently on each card (1..9), keyed by (season a, remoteness b) -----------------
# Chosen so the intended middle row (July, roadside->backcountry) reads 7-2-9 (non-sequential, not a
# guessable keypad run), and all six codes come out distinct.
DIGIT = {
    (0, 0): 3, (0, 1): 8, (0, 2): 1,   # June:   roadside 3, hike 8, backcountry 1
    (1, 0): 7, (1, 1): 2, (1, 2): 9,   # July:   roadside 7, hike 2, backcountry 9
    (2, 0): 5, (2, 1): 6, (2, 2): 4,   # August: roadside 5, hike 6, backcountry 4
}

# --- prose + sender per card (single source shared with make_postcards.py), keyed by (season a, remote b).
# Each message encodes its three attributes experientially (season / remoteness / trip length) without
# naming them as data; the authoritative machine-readable values are the tags printed from the table above.
POSTCARD = {
    (0, 0): ("Snow still packed in the ditches but the sun's up half the night now. Grabbed a day off and "
             "just drove till a pull-off looked good - camera on the dash the whole way, home before dark. "
             "Or what passes for dark in June.", "Priya"),
    (0, 1): ("Breakup's finally done - trail was mud to the knee, but only an hour in from the lot. Pitched "
             "Friday, walked out Sunday. Two nights was just enough to dry the boots.", "Marco"),
    (0, 2): ("The floatplane dropped us Monday and doesn't come back till Saturday. No road within fifty "
             "miles, no bars on the phone, and the light never really goes. Seven days of nobody. Bliss.", "Nadia"),
    (1, 0): ("Peak of summer and every turnout on the highway's got a camper in it. Snagged one right off "
             "the road Saturday, stayed the night, drove home Sunday. Warm enough to sit out in a t-shirt "
             "at midnight.", "Deb"),
    (1, 1): ("Hiked the hour in from the trailhead and just... stayed. Seven days, same little meadow, "
             "wildflowers up to here and the sun on the tent by seven every morning. Didn't want to walk "
             "back out.", "Kim"),
    (1, 2): ("Chartered the little plane just for the day - landed on a gravel bar miles from anywhere, "
             "fished till the pilot came back at six. High summer, hot enough we swam. One perfect day, no "
             "road, no nothing.", "Theo"),
    (2, 0): ("A whole week in the camper, never more than a stone's throw from the highway. First of the "
             "fireweed's gone to cotton and there's a real chill by 2am now. Aurora one night - faint, but "
             "back.", "Sol"),
    (2, 1): ("Quick one - hour up the trail and back before supper, buckets of blueberries to show for it. "
             "Leaves just starting to turn at the tops. Fingers stained for days.", "Ivy"),
    (2, 2): ("Packrafted three days from the nearest road, out over the long weekend. Termination dust "
             "already on the high peaks and the nights properly dark again - summer's turning. Worth every "
             "mile.", "Wes"),
}

# catalogue index printed small on each card ("#n of 9") so the player knows the set is complete. It is
# the enumeration order (NOT the code digit — the digit is scrambled); the two are deliberately different.
def catalog(a, b):
    return 3 * a + b + 1

# variable accessors: given a card (a, b), its level on each of the three variables
VARS = {
    "season":   lambda a, b: a,
    "remote":   lambda a, b: b,
    "length":   lambda a, b: length_index(a, b),
}

CARDS = [(a, b) for a in range(3) for b in range(3)]


def middle_row_code(rows, cols):
    """Facet by rows=X, cols=Y; return the middle row (X-level == 1) read left->right by Y-level."""
    xf, yf = VARS[rows], VARS[cols]
    mid = [c for c in CARDS if xf(*c) == 1]
    mid.sort(key=lambda c: yf(*c))
    return "".join(str(DIGIT[c]) for c in mid)


def assert_pairwise_complete():
    """Property 1: each pair of variables fully crosses (clean 3x3 tiling)."""
    names = list(VARS)
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            xf, yf = VARS[names[i]], VARS[names[j]]
            seen = {(xf(*c), yf(*c)) for c in CARDS}
            assert len(seen) == 9, f"{names[i]}x{names[j]} does not fully cross: {len(seen)}/9 cells"


def all_codes():
    names = list(VARS)
    out = {}
    for r in names:
        for c in names:
            if r != c:
                out[(r, c)] = middle_row_code(r, c)
    return out


INTENDED = ("season", "remote")   # what the two editorial notes pin down
INTENDED_CODE = "729"


def main():
    assert_pairwise_complete()
    assert set(POSTCARD) == set(CARDS) == set(DIGIT), "POSTCARD/DIGIT must cover all nine cards"

    print("Nine postcards (Latin square; C = (season+remote) %% 3):\n")
    print(f"  {'digit':>5}  {'season':<7} {'remoteness':<12} {'length':<10}")
    for a, b in CARDS:
        c = length_index(a, b)
        print(f"  {DIGIT[(a, b)]:>5}  {SEASON[a]:<7} {REMOTE[b]:<12} {LENGTH[c]:<10}")

    codes = all_codes()
    print("\nAll six (rows, cols) pairings -> middle-row code:\n")
    for (r, c), code in codes.items():
        star = "  <- INTENDED (editorial notes: rows=season, cols=remoteness)" if (r, c) == INTENDED else ""
        print(f"  rows={r:<7} cols={c:<7} -> {code}{star}")

    # property 2: six distinct codes
    vals = list(codes.values())
    assert len(set(vals)) == len(vals), f"codes not distinct: {vals}"
    # property 3: the intended pairing gives the keypad code
    assert codes[INTENDED] == INTENDED_CODE, f"intended code drifted: {codes[INTENDED]} != {INTENDED_CODE}"

    print(f"\nOK: 6 distinct codes; intended pairing (season x remoteness) -> keypad code {INTENDED_CODE}.")


if __name__ == "__main__":
    main()
