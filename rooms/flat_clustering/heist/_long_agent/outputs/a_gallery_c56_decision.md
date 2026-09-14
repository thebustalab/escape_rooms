Read all four. Here's the state I established before deciding:

- **Live spec already carries both down-levers pulled.** `sheet.motion.vigour` = "barely stirring… very gently in a slight draught" (the L1/L2 rung), and `motion.phrase` = "breathing very gently, barely lifting at one corner and settling back". Both address Lucas's 2026-09-13 note that the gallery's dust sheet was "too aggressive".
- **The ART note is addressed too** — `other_cases` was added, answering "the cases all empty".
- **The still is current.** `render_prompt(spec)` is byte-identical to the committed `scenePrompt`, and `scene.png` (22:23) is newer than the last spec edit (22:02). It was regenerated from this spec.
- **The motion prompt I was shown is the stale `.txt` fallback**, not what will be used. `render_motion_prompt(spec)` returns the softened phrase; the spec declares a mover, so per step 2 the spec wins and the `.txt` is dead weight (pinned by `test_motion_prompt_source.py`).
- **The only existing clip, `a_gallery_motion_ri11_looped.mp4`, is 19:06 on 09-13** — three hours older than both the spec edit and the still. It is the clip Lucas rejected; it does not belong to this state. Gate report `{}` is correct.

Nothing is left to author before the GPU, so this is a render, not another authoring pass.

DECISION: RENDER
WHY: The spec has a bounded mover with vigour authored down and a softened phrase, the still was regenerated from this exact spec, and the only clip on disk predates both edits — so one render at 3072x1024, end guide 0.70, seed 4242 is the next step.