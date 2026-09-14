I checked this myself rather than trusting the write-up.

**Verified on disk:**
- `_has_authored_mover` (long_agent.py:3549) requires `motion.moves` + `vigour` + `phrase`; the lamp on disk carries only the legacy `animate: {motion, loop}` block. RENDER is refused unconditionally — the worker's read of the deadlock is correct, and no settings lever is proposed.
- I dry-ran the fragment through the runner's own merge path: it resolves to the `lamp` element (index 2, first match on `at`), and `render_motion_prompt` comes out **byte-identical** to `art_prompt_motion/heist/a_vault.txt` — confirmed by comparison, not by assertion. `_has_authored_mover` flips to True.
- `render_prompt` before the fragment == `render_prompt` after: the element sweep is unchanged; splitting the vigour clause out of `desc` and back in via `element_desc` is a round trip.
- The still depicts the mover: a caged lamp on a long flex hanging just left of centre, warm against the box wall. **Bounded**, not frame-filling. Both extreme edges are the same riveted steel; `seam.needsWork` is false.
- The mover *has* been rendered — 24 clips in `temp/cine/_art_prompt_exp/heist/` from 2026-09-11, off this exact motion prompt, and the ledger entry the worker cites is verbatim (`notes/cinemagraph_ledger.md`: a_vault 0.77 / 0.91, "strongest numbers measured anywhere"). So the "AUTHOR_MOVER on a never-rendered mover" bar does not bite; in the spec's own terms there is no mover yet at all, and this fragment authors the first one.
- No clip is accepted, no zero-return reasoning, no hand-written art prompt, and `a_vault` has zero hotspots and no `image` key — nothing committed is touched.

**One correction to the worker's account, not disqualifying:** `render_prompt` is *not* byte-identical to the committed `scenePrompt`. That stored string predates later boilerplate additions (the EQUIRECT paragraph, STYLE, EDGE_DISCIPLINE, the ground-is-one-surface clause), so the runner's unconditional `scenePrompt` rewrite will change it. That drift is inherent to every AUTHOR_MOVER in this runner, not to this fragment — the authored content is untouched, which is the load-bearing claim and it holds.

The `touch` advice is sound: needs_still clears at long_agent.py:3673 on `scene.png` mtime > `spec_edited_at`, and since the depicted content is unchanged, regenerating would only risk a human-triaged seam-clean still.

VERDICT: PASS