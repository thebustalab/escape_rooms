Verified independently against the files, not the worker's summary.

**Checks that hold:**

- **Spec on disk matches the handed spec.** `scenario.json` → `rooms[shears].authoring.sceneSpec`: `blade_spout` is the only element carrying a `motion` block with all three of `moves`/`vigour`/`phrase`; `lenticulars` carries only legacy `animate`. `_has_authored_mover()` returns True.
- **The motion prompt is spec-derived, not hand-written.** I ran `SS.render_motion_prompt(spec, rigid=True)` against the live spec — it reproduces `art_prompt_motion/beacons/shears.txt` exactly (65 words, one mover named, one-item rigid clause naming only the spyglass/tripod/survey sheet). The file's mtime 00:19 matches progress.md line 305, the PIN_NON_MOVERS that wrote it.
- **The still depicts the mover.** I looked at `shears/scene.png` (3072×1024, 01:20) at native crop. Water issues from the blade face at head height, arcs clear and falls into a basin with visible splash and wet dark rock — the authored vigour is rendered. Bounded at roughly 16% of frame width, not frame-filling.
- **No clip against this art.** The held clip `shears_motion_ri61_looped.mp4` is 00:33; `scene.png` was restamped 01:20, 47 minutes later. `rooms.shears` is `{}`. This is exactly the case `state.json`'s `review_note` describes, and its instruction is "render each ONCE against the art as it stands and gate."
- **The RENDER code path is safe here.** `needs_still` is unset (empty room record), so the regenerate guard won't fire — which the review_note requires. RENDER writes nothing to `scenario.json`; the `at`-keyed merge that broke kiln is only reachable from the authoring branches.

**None of the rejection criteria are met.** No settings change proposed — 0.70 is the plan's existing `end_guide`, and the falsified sweep (the whole Sep 10 `le045`–`le080` × seed grid sitting in `_art_prompt_exp/`) is not being re-entered. The mover is bounded. No zero return is used as evidence — there is no gate report at all. No clip is accepted. Nothing is hand-written. The decision isn't AUTHOR_MOVER.

**One thing to note for later, not a blocker:** `path_hood` and `blade_spout` both carry `at: "to the left"`. That's the same duplicate-`at` collision that corrupted kiln's fragment merge at `long_agent.py:4184`, and the door sorts first. RENDER never touches that code, so it's inert this cycle — but if shears ever comes back needing AUTHOR_MOVER or ADJUST_VIGOUR, the fragment will land on the door.

VERDICT: PASS