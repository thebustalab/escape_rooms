I verified the worker's chain independently rather than take it on trust: I extracted the 338×102 lamp box from all three renders, confirmed at 4× zoom that it really does sit on the village lights (tiny warm specks, ~46–50 warm pixels, 0.13% of the box), and re-ran the pipeline's own `motion_spec.measure_subjects` on each file.

**The measured chain (my run, judge's own metric):**

| file | village_lamps p95 | verdict |
|---|---|---|
| `cine_night_src.mp4` (unpatched base) | **4.23** | dead |
| `cine_night_raw.mp4` (post-patch) | 3.18 | dead |
| `cine_night.mp4` (shipped) | 2.77 | dead |

`DEAD_P95 = 4.5` (`motion_spec.py:58`).

The worker's diagnosis is real and well-grounded — it looked, and the patch tile genuinely did destroy lamp motion (my p-p numbers: 7.7 → 4.2 → 2.9, matching its 7.0/5.6/2.1). But its proposed action fails on its own arithmetic.

---

Your diagnosis is sound and independently reproduces — the `village_lamps` tile really did suppress motion the base render had, and the box really is aimed at the lamps. But your proposed REBAKE cannot clear the reject: I re-ran `measure_subjects` on `cine_night_src.mp4` and the unpatched base scores p95 **4.23**, already under `DEAD_P95` 4.5 before the loop crossfade takes its ~0.87 cut (landing near 3.7), so a de-patched rebake ships a clip the judge rejects for the identical reason and burns a cycle. You argued this yourself — "geometrically incapable of moving p95 past the 4.5 dead threshold even at perfect flicker... a spec/measurement mismatch for Lucas to settle" — which is a PARK conclusion attached to a REBAKE action. Re-submit as **PARK**, carrying the drop-patch finding as the note for Lucas (worth adding: dropping the tile also lifts `river_glimmer` from weak 6.73 to alive 8.53, so the rebake is still the right thing to do *once he rules on the lamp threshold* — just not as the answer to this reject).

VERDICT: FAIL