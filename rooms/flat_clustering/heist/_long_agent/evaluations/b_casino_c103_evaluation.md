I verified every load-bearing claim against the files and code rather than the write-up.

**Confirmed independently:**

- **Gate report is stale.** scene.png committed 15:04:36; ri98 rendered 14:53. The report describes superseded art.
- **The duplicate is real.** The committed spec carries two elements with `id: "smoke"`, both `moves: true`. The written motion prompt at art_prompt_motion/heist/b_casino.txt names the same cigar twice, the second phrase carrying "slowly and steadily" and "very gently".
- **Art prompt is byte-identical under the edit.** I ran both specs through scene_spec.render_prompt: `ART IDENTICAL: True`. This holds because element_desc (scene_spec.py:387) appends vigour only when `moves` is true, so folding it into `desc` is exactly neutral.
- **So needs_still cannot fire.** long_agent.py:4196 gates it on `render_prompt(spec) != prompt_before` only. The good 15:04 still survives and the art budget is untouched.
- **The budget really is spent.** state `generations: 3` against plan `max_generations: 3` — any art-prompt change parks the job (long_agent.py:4034). The per-room `art_generated: 2` is a different counter; the worker's claim was right.
- **Motion prompt collapses correctly** to the single bounded phrase with "Only that moves", no rigid switch (`rigid=(d == "PIN_NON_MOVERS")` → False; no `still_as` anywhere), and `_has_authored_mover` stays true, so the next cycle can render.

**On the one criterion that could have bitten** — AUTHOR_MOVER on a mover never rendered. I checked the timeline in progress.md: ri98 was rendered 18:45 UTC, the two-phrase prompt file was written 19:02 UTC by cycle 100. So ri98 rendered the *single* slow-bank mover, and it measured peak 3.78. The element being demoted is precisely the one with rendered evidence against it; the untested bounded plume is left byte-for-byte untouched. The criterion does not apply.

Two hazards the worker didn't name, which I checked and found harmless: the SPEC is a dict carrying `"elements"`, so it hits the wholesale-replace branch (long_agent.py:4157) and never reaches the per-`at` matcher — which would otherwise have been ambiguous with two identical `id`/`at` pairs. And the deep-merge of `motion` is bypassed for the same reason.

The worker's non-blocking flag is accurate: the stale clause does remain in the *art* prompt, contradicting its own "no smoke layer across the room" negation. It is inert while no redraw happens, and removing it now would change render_prompt, set needs_still, and park the job. Leaving it and flagging it is the right call under the spent budget.

No settings change, no frame-filling mover, no reasoning from the zero return, no clip acceptance, no hand-written art prompt. The edit is zero-cost and makes the next render a clean test of the one untested mover.

VERDICT: PASS