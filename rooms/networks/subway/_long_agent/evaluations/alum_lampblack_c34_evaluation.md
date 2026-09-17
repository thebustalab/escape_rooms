I checked every load-bearing claim against disk rather than the worker's account.

**The harness fields are wrong, and the worker is right about why.** "Clip: none yet / Gate report: {} / Tried already: []" reflects the round-3 state.json, where alum_lampblack carries only `{"retries": 1}`. The archived round-2 state shows cycle 49 decided RENDER at ~13:50; that render landed at 13:53 and the job was archived before it could record the result. Three clips exist (ri8, ri63, ri49), all at byte-identical params.

**Verified independently:**

- *Prompt* — I imported scene_spec and resolved it from the live scenario.json. It comes back byte-for-byte as the worker quoted it. Only `soot_lamp` has a `motion` block; `grating_light` carries an `animate` block, which `render_motion_prompt` does not read, so exactly one mover reaches the render.
- *Gate report* — the round-2 render log matches the worker's figures exactly: camera still, return 0.0, glitch breadth 0.062 raw / 0.042 normalised, dead ratio 17.93 / peak 25.02, dead false, verdict "survived gates — needs Lucas's eye."
- *Source still* — the previous gatekeeper's 9.9-vs-12.7 margin was thin enough to be worth redoing. I pulled frame 0 and diffed against all four stills: scene.png wins at 9.87, and the margin *widens* to 10.02 vs 13.61 when the mover column is masked out — the right direction, since the residual against the true source outside the mover should be compression noise alone. Timing agrees: scene.png written 13:44:21, render begun 13:45.
- *The frames* — I looked at the strip. The diff panel puts the moving energy on the flame and its smoke column and essentially nowhere else; train, spiral stair, rails, tiling and floor are static. Flame shape and plume clearly differ across frame 0 / mid / last. Not dead.

**Against the reject list:** no settings change, mover is bounded rather than frame-filling, the zero return is explicitly named as the cyclic-flow ambiguity rather than treated as death, no prompt hand-writing, and AUTHOR_MOVER isn't proposed. HOLD does not accept anything — the precedent rooms in this same state.json (ochre_woad, ochre_verdigris, both 0.0 return) show HOLD writing only `held: true` plus a staged path under _scratch/cine_cand/, never scenario.json's committed art or hotspots. That is the PARK-for-a-human-eye path the rules endorse.

One thing for Lucas's eye when he gets there, which I found and the worker did not flag: the committed still draws the lamp **enclosed in a glass lantern**, while the spec insists on an open pan with "NOTHING in front of it — no glass, no shield, no grille." That's a real art divergence, but it's a stills question, not this cycle's, and the job's own review note settles the art for this room ("round-2 art is already committed and good to render — it needs a clip only, NOT new art"). HOLD is precisely the decision that routes it to the one person who can call it.

A fourth run at the same seed, still and prompt reproduces ri49 and buys nothing.

VERDICT: PASS