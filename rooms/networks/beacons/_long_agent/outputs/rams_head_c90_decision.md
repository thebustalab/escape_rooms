I have what I need. Verified rather than assumed:

- **The spec already carries a bounded mover.** `melt_ribbon` has a full `motion` block (`moves`/`vigour`/`phrase`), so `_has_authored_mover` sees it — no legacy-`animate` blind spot here.
- **The motion prompt in the brief is stale.** I ran `scene_spec.render_motion_prompt` on the live spec: it resolves to *"…The ribbon of meltwater falling clear from the notch above and dropping past the edge of the shelf, braiding and coming apart as it goes. Only that moves…"* — 42 words, house form, naming the waterfall. The cat's-paws-on-the-tarn text quoted to me is the `art_prompt_motion` fallback, which the renderer will not reach because the spec declares a mover. Nothing to fix.
- **The still depicts it.** `scene.png` (3072×1024, regenerated 2026-09-14 21:59, after the re-authoring) shows a tall falling-water column on the left at roughly x 0.06–0.28 — bounded and hard-edged, not frame-filling, and falling water is a confirmed-alive mover category in the ledger. The tarn behind it is frame-filling and is *not* named in the prompt, which is the right way round.
- **No clip exists against this art.** `cine_base.mp4` dates to 2026-09-09, before the melt-ribbon re-author. Gate report is empty, nothing tried.
- Seam is clean on the current image: `seamBandRun` 0.004, `needsWork` false, screened 2026-09-15.

Spec, prompt and still are consistent and none of the fix branches applies — the room has never been rendered in this form.

DECISION: RENDER
WHY: The spec carries one bounded authored mover (`melt_ribbon`) whose vigour is depicted in a freshly regenerated 3072 still, the motion prompt resolves from that spec to a 42-word house-form prompt naming only the waterfall, and no clip yet exists against this art.