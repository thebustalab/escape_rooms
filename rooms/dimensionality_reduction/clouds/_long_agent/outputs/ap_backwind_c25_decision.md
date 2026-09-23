Read the pipeline, the ledger, `scene_spec.py`, and the room's committed art and spec.

**What I found**

- The spec already carries a bounded mover: element `derelict` at `to the right` (a closed-vocabulary position), with `motion.moves: true`, `vigour: "loose and restless, billowing and snapping"`, and a phrase. So `_has_authored_mover` sees it.
- The committed `scene.png` is in sync with the spec — `scene_spec.render_prompt(sceneSpec)` reproduces `authoring.scenePrompt` byte-for-byte, and that prompt does carry the EQUIRECT clause (my first grep was case-sensitive; it's there).
- The still genuinely **depicts** the mover. I cropped x≈0.80 of the 3072x1024 panorama: a second glider rides alongside with one membrane wing visibly shredded — ragged, holed, tattered trailing edge, spread loose. Bounded (roughly a sixth of the frame width, well clear of both edges), cloth-like, and torn membrane is the same class of mover as the tarpaulin/dust-sheet/drape cases already evidenced.
- `render_motion_prompt` returns a clean 30-word house-form prompt naming only the wing: *"locked-off static camera, zero camera movement. The derelict glider's torn membrane wing flapping and billowing in the wind. Only that moves; everything else stays perfectly still. Seamless natural loop."* Flapping/billowing is oscillatory, so the no-travel rule is satisfied — it names the wing, not the glider.
- No clip exists, gate report is empty, nothing tried. Nothing to soften, nothing to pin — the rigid escalation is a scalpel reached only after a clip shows the wrong thing moving, and pre-loading it is the documented cause of camera drift.

Nothing left to author before the GPU.

DECISION: RENDER
WHY: The committed still already depicts a bounded, authored-vigour mover — the derelict glider's torn membrane wing — and the spec renders a compliant 30-word oscillatory motion prompt, so the only thing missing is the one render.