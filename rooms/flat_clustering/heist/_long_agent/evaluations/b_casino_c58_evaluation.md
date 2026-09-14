Verified every load-bearing claim against disk rather than the worker's account. All of them hold.

**Timestamps (the decisive fact).** `b_casino_motion_ri14_looped.mp4` — 2026-09-13 19:23:33. `scene.png` — 22:23:56. `scenario.json` — 22:24:26. The only clip predates both by three hours, so it animates the pre-feedback still under the pre-feedback prompt. Confirmed.

**The soften landed on both levers.** Diffing the `lucas_feedback` backup against live: `vigour` "coiling and rolling slowly" → "drifting very slowly, barely moving in the still air"; `phrase` rewritten to "rising slowly and steadily … spreading very gently"; and a new `ashtray` element added. The mover went from "a heavy bank of cigarette smoke" to a thin ribbon off a depicted cigar — strictly **narrower**, which is the opposite of the frame-filling failure mode.

**Not a settings change.** 3072x1024 and end guide 0.70 are the hard-coded pipeline defaults (`cinemagraph_tools/cine_render.py:8,43`) and `plan.json`'s own `end_guide`. Restating the sanctioned pass is not proposing a lever.

**Zero return handled correctly.** The decision pre-emptively warns *against* reading 0.00 as dead, and `notes/cinemagraph_ledger.md` backs it: b_casino is tabulated as `**cyclic flow** (smoke)` at 0.00/0.00, explicitly contrasted with hood, which Lucas confirmed by eye as genuinely dead. That's the inverse of the rejection criterion.

**The stale-prompt flag is real and correctly scoped.** `art_prompt_motion/heist/b_casino.txt` is dated 2026-09-10 and carries the un-softened wording — but `exp_art_prompt.motion_prompt` resolves the spec first and falls back to `.txt` only if the spec yields nothing (`exp_art_prompt.py:86-106`). heist is migrated, so the softened phrase is what renders. Display staleness only; the worker didn't propose editing it or hand-writing a prompt.

Two things the gate report's emptiness hides, worth carrying forward: b_casino already produced a RENDER decision at 02:59 UTC that drew REVIEW and was never acted on, then burned three cycles on the permission-rule crash — so "Tried already: []" understates the history, but nothing was ever rendered, which makes this the unblocking call rather than a repeat. And `plan.json`'s third done-criterion positively *requires* this render: "no clip animates a still that predates its own motion prompt" is precisely what ri14 does today.

No rejection criterion fires. The decision proposes RENDER on a mover that has never been rendered — which is what criterion 6 demands instead of AUTHOR_MOVER.

VERDICT: PASS