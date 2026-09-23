I checked every claim against the files rather than the write-up.

**Verified independently:**

- **Art in sync with spec** — `scene_spec.render_prompt(sceneSpec)` is byte-identical to the committed `scenePrompt`, both 11,887 chars. The still cannot predate its own motion prompt.
- **Spec shape** — `kite` is element index 3, at the head of the `dead ahead in the centre` slot, and is the **only** element carrying `motion`. The other six have none.
- **The still depicts the mover** — I cropped the centre band at native resolution. There is one pale veined membrane kite on a single taut line running down to the nose tip, ribbon tail streaming below. Roughly 130 px across in a 3072×1024 frame: bounded, near-field, high contrast against the dark eyewall. The full-panorama sweep shows no duplicate — the singularity guard held.
- **Nothing was lost to the regeneration** — the dash still carries sampler globe, milky reading-pane and the six-cell triangle beside the lever; `eye_knot` one slot left is a lumpy closed clot of bruised cloud over the city's heart, no spiral, no eye.
- **Motion prompt** — rendered it through `exp_art_prompt.motion_prompt`: 34 words, house form, one mover named. "Riding and dipping on its line… ribbon tail rippling" is tethered and oscillatory; `notes/cinemagraph_pipeline.md` §THE NO-TRAVEL RULE lists *rippling* on the Name-only side and names nothing here that crosses frame.
- **State** — `state.json` for `ap_stillstand` has `art_generated: 1`, no `attempts`, no `last_gate`, no `clip`; no mp4 exists under `temp/cine` or `_scratch/cine_cand`. Genuinely un-rendered.

**Against the reject list:** no settings change (end guide 0.70 is `plan.json`'s committed value, not a proposed lever); the mover is bounded, not frame-filling; no gate metric exists to misread; nothing is accepted and nothing written to committed art or hotspots; the prompt is spec-derived, not hand-written; and the decision is RENDER, not AUTHOR_MOVER — it explicitly declines to re-author a mover that has now been correctly depicted but never animated.

The c13 re-authoring did what it was meant to do, and the one remaining step is the single render.

VERDICT: PASS