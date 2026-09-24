I checked the worker's claims against the files rather than its description. Every one holds.

**Verified independently:**

- **Spec movers** — the cockpit sceneSpec carries motion on exactly two elements: `city` ("brightening and dimming in place") and `eyewall` ("lightning rippling slowly through the storm cloud"). `sampler` has a sound block only, no motion; none of the other retired heroes appear. That is the human-mandated pair, not a re-author.
- **Motion prompt** — I resolved it myself through exp_art_prompt.motion_prompt rather than trusting the quote. It comes back byte-identical to what the worker reported, 38 words, spec-derived. There is no art_prompt_motion/clouds/cockpit.txt override, so nothing hand-written is shadowing the spec. Both phrases are pure light modulation; no travel verbs.
- **Still freshness** — spec edited 06:59:39, scene.png written 07:01:05, scenario.json 07:01:06. The still post-dates its own motion prompt, so the "no clip animates a stale still" criterion is satisfied.
- **The image itself** — I looked at it. The lit city heap fills the left with the colour living in the buildings (filament, honeycomb, stained glass, the three shadow kinds), lightning crawls the eyewall ledge on the right, the palette is grey elsewhere, and the dash, sampler globe, reading-pane and the triangle of dark override cells are all sharp in the foreground. Both movers are genuinely depicted.
- **heightPass** is `level` / `cloud: false` on `_world/plate.png`, matching worldPlateRef — so this is a room that should show full lightning and city, and does.
- **Settings** — seed 4711 and end guide 0.70 are already pinned in plan.json. The worker reports them; it does not propose changing them or anything else.

**Against the reject list:** no settings change, no frame-filling re-author (the two movers are the approved recipe, each bounded to its own half and light-only), no zero-return reasoning (no clip exists at all), no acceptance and no write to committed art or hotspots, no hand-written prompt, and not AUTHOR_MOVER on an unrendered mover.

One note that does not block this cycle: stale hand-written motion txt files still sit in art_prompt_motion/clouds for ap_backwind, ap_pileup and ap_stillstand. The spec wins over them while those specs carry motion, but they are worth clearing before those rooms come up.

VERDICT: PASS