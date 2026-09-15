I checked the frames and the spec directly rather than the worker's account.

**The still (3072×1024, `rooms/networks/beacons/spindle/scene.png`).** The needle carries a clear, well-formed spindrift banner tearing off the crest and feathering downwind. It is genuinely bounded — it occupies roughly x 0.24–0.37, left of centre, against otherwise empty cobalt sky. This is the opposite of the `hood` frame-filling failure, and it means the mover is *depicted*, not implied (the ledger's own art rule from the verdigris/madder notes).

**The spec.** `name_crag` carries a complete `motion` block (`moves`/`vigour`/`phrase`), so the room is post-migration and visible to `_has_authored_mover`. The `motionSpec` hero subject `needle_spindrift` has box `[0.24, 0.03, 0.37, 0.32]` — bounded, and it matches where the spindrift actually sits in the image. `survey_sheet` is pinned `still`, and the pinned/negatives lists hold the cold fire-basket and the flat survey sheet.

**The prompt.** `cinemagraph_tools/art_prompt_motion/beacons/spindle.txt` is the house form — locked-off camera, the spec's own `phrase` verbatim, "only that moves", seamless loop. Spec-derived, names one mover, nothing hand-written.

**"No clip exists" is correct in this loop's terms.** The `cine_base.mp4` files in the room directory belong to the earlier pipeline (last touched 2026-09-07). This instance started 2026-09-14 22:51 UTC, renders into `temp/cine/_art_prompt_exp/beacons/`, and `state.json` has no `spindle` entry at all — zero attempts, no gate report. The plan's own instruction for this run is "Render each ONCE and gate", and the review note confirms all twelve stills just cleared `seam_stage --step auto` (spindle's seam block is stamped 2026-09-14T18:50:52, `needsWork: false`, human-accepted 2026-09-03). So the still is current and regenerating it would throw away a hand-accepted panorama for nothing.

**Against the reject list:** no settings touched (it renders at the plan's 0.70 and explicitly declines to chase seeds); the mover is bounded, verified in the pixels; no zero return is invoked — the gate report is empty; nothing is accepted and nothing is written to committed art or hotspots; the prompt resolves from the spec; and it is RENDER, not AUTHOR_MOVER on an unrendered mover. None fires.

One thing worth flagging to Lucas rather than to the runner: the spec's `seamOccluder` describes a full-height timber signal mast, and the committed still has no mast at the seam — the seam is bare snow-slope. He accepted that seam by hand on 2026-09-03, and the seam gate reads clean, so it doesn't block this render; it's a spec-vs-art divergence to settle later if the mast is still wanted.

VERDICT: PASS