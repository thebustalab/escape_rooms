I verified every load-bearing claim against disk and the frames rather than the write-up.

**Confirmed independently:**

- **The prompt provenance is right.** Running the renderer's actual path (`exp_art_prompt.motion_prompt('heist','a_opera',room_rec)`) returns the spec-derived prompt at **57 words**, pinning only "the panelled walls and the gilded box parapet". The 104-word `art_prompt_motion/heist/a_opera.txt` is unreachable fallback, as claimed.
- **The 12:00:16 edit is real and is exactly what the worker described.** Walking the backup chain (the filenames carry the backup *creation* time, the mtimes the pre-edit content), `bak_20260914_120016_feedback_round2` holds `phrase: "only the heavy crimson velvet swag curtain… stirring gently in a draught, its folds shifting and settling"`; current holds `"…breathing very slightly, its folds barely shifting"`. `vigour` and `rigid` are untouched, and `rigid` is still the two-item clause — Lucas's "do not lengthen it" is honoured.
- **No still is owed.** `render_prompt(spec)` is byte-identical to the stored `scenePrompt` (3129 chars, `True` on direct comparison), so `needs_still` correctly does not fire. The only 12:29 change to a_opera was a bookkeeping timestamp; the substantive part of that write was b_casino's new art.
- **`movers(spec)` returns exactly one mover, `swag`** — bounded, not frame-filling.
- **ri75 predates the softening.** Baked 11:48–11:50; the phrase changed after 12:00:16. The softened prompt has never been rendered.

**On the frames.** My own per-column temporal-std profile over ri75's 73 frames puts all motion at x≈0.26 (swag band mean 7.17, peak 13.77) against a ~1.4–2.5 baseline elsewhere; both right-hand door bands are the quietest in the panorama (1.35 and 1.49). The strip confirms it by eye — frame 0, mid-loop and last frame are near-identical, both doorways stay open with the stair visible throughout, and the difference map lights only on the swag and the parapet rail. The drape that swallowed a live door hotspot in ri61 is genuinely absent. So ri75 was a clean clip whose only open question was liveliness, and that question is the one Lucas answered.

I also checked the stale `last_eval` still sitting in `state.json` — it describes ri61's door-swallowing defect and prescribes lengthening the rigid clause. That prescription was tried (ri73), produced CAMERA MOVES, and was reversed by Lucas at 11:35. It is superseded, and the worker is right not to act on it.

**Against the rejection list:** no settings proposed (end guide comes from `plan.json`, and ri61/ri73/ri75 params are byte-identical anyway); the mover is bounded; no zero-return reasoning appears; nothing is accepted and nothing is written to committed art or hotspots; the prompt is rendered from the spec rather than hand-written — the worker explicitly declined SOFTEN_PROMPT to avoid overwriting Lucas's wording; and it is RENDER, not AUTHOR_MOVER.

Two inaccuracies, neither load-bearing: the worker repeats "176 words" for ri73's prompt, which a prior cycle measured at 104 (it was quoting Lucas's own note), and it truncates the old phrase when quoting it. Its flagged side-issue is also legitimate — the brief-builder does quote the stale `.txt` while the renderer resolves from the spec.

The decision matches Lucas's instruction to render each room once and gate it.

VERDICT: PASS