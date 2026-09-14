I checked each claim against the tree rather than the write-up.

**Verified true:**
- `briefing`'s `window` element carries a full `motion` block (`moves`/`vigour`/`phrase`) in the live `scenario.json`, so `_has_authored_mover` (long_agent.py:3549, which requires all three) returns True and the RENDER gate at long_agent.py:3926 will not refuse.
- The 2026-09-13 `animate` migration was lossless: it lifted "rain running down the near glass in heavy sheets" out of `desc` into `motion.vigour`, and `scenePrompt` is **byte-identical** to the pre-migration version. So the committed still was produced by the prompt the spec still renders — no hidden `needs_still` condition (and `state.rooms` is `{}`, so the flag isn't set).
- The art genuinely depicts it. At native resolution the window bank shows dense vertical rain streaking and beading across all three bays with the city smeared behind. This is not a spec asserting motion the art doesn't supply.
- **Bounded.** The window bank occupies roughly x 0.12–0.30 of the 3072-wide panorama — one wall of a five-element room, not frame-filling. (The worker said 0.11–0.23; it's a little wider than that, but nowhere near the frame-filling failure mode.)
- I ran `scene_spec.render_motion_prompt` on the live spec myself. It emits exactly the 28-word prompt quoted, naming only the rain: *"locked-off static camera, zero camera movement. Rain running down the near window glass in continuous slow rivulets. Only that moves; everything else stays perfectly still. Seamless natural loop."*
- No clip exists. No `briefing.txt` in `art_prompt_motion/heist/` (only a_gallery, a_vault, b_casino, b_docks), no `briefing_*` artifacts in `temp/cine/_art_prompt_exp/heist`, no mp4 in the room dir. "Motion prompt: NONE" means no committed `.txt`, not no prompt — the spec fallback was wired today and works.

**Against the reject list:** no settings change (the render uses the plan's own `end_guide` 0.70); the mover is bounded; zero return is flagged as ambiguous, not dead — the opposite of the failure mode; RENDER launches `cine_room` and writes nothing to committed art or hotspots; the prompt is spec-derived, not hand-written; and it isn't AUTHOR_MOVER on an unrendered mover.

The worker's caution stands on its own: rain is cyclic flow, so `cine_return_check` will likely score near zero, and the state file's own review note pre-flags exactly this family. That must escalate, not trigger a re-author.

Nothing has reached the GPU and the authoring is already correct, so the one render is the right next move.

VERDICT: PASS