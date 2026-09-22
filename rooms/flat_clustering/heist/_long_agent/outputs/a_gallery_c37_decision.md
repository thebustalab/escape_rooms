Evidence read. I measured the two existing raw renders of this room against each other rather than re-running anything — same seed, same end guide, same 73 frames, so it is a like-for-like within-room comparison.

**The clip is not dead, it is over-quenched.** In the dust sheet's own band (x 0.28–0.44, where `_x_from_at` puts "just left of centre"):

| | sheet-band excursion peak | band return | sheet temporal std (mean/max) | sheet-vs-whole-frame peak ratio |
|---|---|---|---|---|
| `ri11` — the still Lucas called **"too aggressive"** | 4.81 (arc, frame 29) | 0.68 | 2.88 / 80.7 | **2.12** |
| `ri35` — current | 2.30 (broad bump, frame 42) | 0.33 | 1.34 / 31.1 | **1.35** |

There is a real localised arc in the sheet, so the gate's 0.00 whole-frame return is the ambiguous reading it warns about, not a death certificate. But the amplitude is less than half of ri11's and the mover now barely separates from the frame's own global shimmer (1.35× against 2.12×) — which is the regime `notes/z_archive/report.md` (archived) describes as reading as texture drift rather than movement, and it matches the gate's peak of 3.62, below every labelled clip in the ledger bar b_casino's smoke.

The cause is visible in the spec: after Lucas's "too aggressive" note **both** softening levers were pulled at once — the depicted vigour went to "barely stirring… very gently in a slight draught" *and* the motion phrase to "breathing very gently, barely lifting at one corner". The evidence says intensity language works down only, so the recovery has to come from the vigour in the still; the phrase just needs its dampers removed, not strengthening past neutral. I dry-ran the fragment through `scene_spec`: it merges onto element index 2 (`sheet`), `movers` stays at one, and both prompts render clean.

One render remains in this room's budget (`attempts` 1 of `max_attempts_per_room` 2).

DECISION: ADJUST_VIGOUR
SPEC: {"id": "sheet", "at": "just left of centre", "desc": "a canvas dust sheet draped over a near plinth", "motion": {"moves": true, "vigour": "caught in a steady draught, one corner lifted clear of the plinth and the near fold swelling, the canvas midway through a slow rise", "phrase": "the canvas dust sheet over the near plinth lifting in a slow draught, one corner rising clear of the plinth and the folds settling back"}}
WHY: The bounded cloth mover is alive but over-quenched — both the depicted vigour and the motion phrase were softened at once after the "too aggressive" note, halving the sheet's excursion from 4.81 to 2.30 and dropping it to 1.35× the frame's own shimmer, so the vigour goes back to a middle depiction and the phrase loses its dampers without being pushed past neutral.