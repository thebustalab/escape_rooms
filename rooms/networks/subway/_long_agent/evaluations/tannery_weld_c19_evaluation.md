I checked the worker's claims against the files rather than its summary.

**Verified independently:**

- **No clip exists for this still.** `tannery_weld/` holds only `scene.png` + undo copies; the previous candidate (`base__ri31.mp4`) was moved into `z_archive/pre_regen3_tunnels_20260917/cine_cand/` at today's regen. Live `cine_cand` is empty for this room.
- **The still is current and depicts the mover.** `scene.png` is 3072×1024, written today 15:10. I cropped the mover band and looked: the row of oiled canvas sheets is there, hung singly with air and lamplight between them, every sheet leaning the same way with hems lifted clear of vertical — the authored `vigour` rendered faithfully. In the full panorama the row occupies roughly x 0.44–0.78 in one upper band. **Bounded, not frame-filling.**
- **No prompt drift.** I ran `SS.render_motion_prompt` on the live spec and diffed it against `art_prompt_motion/subway/tannery_weld.txt` — byte-identical. `exp_art_prompt` reads that file for the render (`test_motion_prompt_source.py` exists precisely to pin this), so the render will use the spec-derived phrase.
- **"Default" really is the default.** `cine_room.py:116` sets `--end-guide` default `"0.70"`, and line 156 hardcodes `--width 3072 --height 1024`. Naming those is not a settings change.
- **State is clean.** Job state has `rooms.tannery_weld = {"art_generated": 1}` — no `needs_still`, no history, so RENDER won't hit the stale-still park.

**Against the reject list:** no settings lever proposed; mover is bounded; no zero-return-as-death reasoning (the 0.23 return is cited as a past pass, not a death call); it accepts nothing and writes nothing to committed art or hotspots; the prompt is spec-derived, not hand-written; it isn't an AUTHOR_MOVER.

Two trivial inaccuracies that change nothing: the prompt is 38 words, not 37, and `motionSpec.subjects[0].phrase` ("swaying heavily…") does differ from the element's `motion.phrase` — but that field only feeds gating/measurement, not the render prompt, so the worker's "cannot have drifted" conclusion holds for the thing that matters.

VERDICT: PASS