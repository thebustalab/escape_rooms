Verified everything independently rather than on the worker's word:

**The gate report is stale.** The only shears clip on disk is `ri57`, written 00:01:52 and looped 00:03:08. The gate JSON quoting those exact numbers (`cine_room_20260915_000350.json`) was written at 00:03:50. Cycle 60's pin landed at **00:19:06** — both `scenario.json` and the motion prompt file carry that timestamp. So the clip on the table was rendered eighteen minutes before the fix existed. The pin has never been rendered.

**The pin is live and correctly scoped.** I re-ran both renderers against the on-disk spec: `render_prompt(spec)` is byte-identical to the committed `scenePrompt`, so the still is untouched and `needs_still` is unset — RENDER won't park. `render_motion_prompt(spec, rigid=True)` returns exactly the 65-word prompt sitting in `art_prompt_motion/beacons/shears.txt`: one mover (the spout), spyglass and survey sheet pinned rigid.

**The render will actually use it.** This mattered — the room also carries a legacy `motionSpec` naming a *different* hero (`lens_cloud`). But `exp_art_prompt.py:86` resolves from `authoring.sceneSpec` first and flips `rigid=True` automatically because `spec["rigid"]` is now truthy. The legacy spec is never consulted.

**The frames back it up.** The committed still (23:48, before ri57 — so not stale) plainly shows the meltwater spout arcing from the crack into its basin: bounded, near, vigorous falling water. And in the clip itself the defect is real — at frame 5 a blue-white plume is firing out of the spyglass muzzle across the villages, and by frame 60 it's gone but the muzzle has visibly warped. That's a rigid-pin failure exactly, and it also proves the clip isn't dead; the appear-and-vanish artefact explains the cyclic-flow reading the gate flagged.

Against the reject list: no settings touched (end guide 0.70, seed 4242, all else unchanged), mover is bounded not frame-filling, the 0.01 return is explicitly not read as death, nothing accepted, no hand-written art prompt, and the decision is RENDER rather than AUTHOR_MOVER. Budget holds at `attempts` 1 of 2.

One small correction to the record, which changes nothing: cycle 60 logged the jet as starting at frame 15; it's visible by frame 5.

VERDICT: PASS