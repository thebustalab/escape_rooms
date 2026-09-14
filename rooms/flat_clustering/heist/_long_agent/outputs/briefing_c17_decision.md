I read the four documents, then checked the room against them rather than against the summary.

**What I found.** `briefing`'s spec already carries a bounded mover that survives the tests the loop cares about:

- `window` has the full `motion` block (`moves` / `vigour` / `phrase`), so `_has_authored_mover` passes — it was caught by the 2026-09-13 heist migration, not left behind in a legacy `animate` block like b_docks was.
- The committed still genuinely **depicts** it. The committed `scenePrompt` carries "rain running down the near glass in heavy sheets", and the 3072×1024 render shows it: dense vertical streaking and beading across the window bank, city lights smeared behind. This is not a spec asserting motion over art that gives it nothing.
- It is **bounded** — the window bank spans roughly x 0.11–0.23 of the panorama, nothing like `hood`'s frame-filling cloud sea. Rain on glass is also in the confirmed-mover family (falling water / water surfaces), and it is flow, not travel across the frame.
- `render_motion_prompt` already yields the house form from the spec, so "motion prompt: NONE" means no committed `.txt`, not no prompt: *"locked-off static camera, zero camera movement. Rain running down the near window glass in continuous slow rivulets. Only that moves; everything else stays perfectly still. Seamless natural loop."* ~30 words, names the mover and nothing else.
- No clip exists anywhere — no mp4, no verdict, empty gate report.

So the art is authored, the prompt is right, and nothing has reached the GPU. There is no re-authoring to do and nothing to soften. One note for whoever reads the verdict: rain is a **cyclic** mover, so `cine_return_check` will very likely score ~0.00. That is ambiguous, not dead — the state file's own review note flags exactly this for briefing's family. Do not read a zero return here as a reason to re-author.

I have not pre-emptively pinned the two lamps. The fix order is explicit that pinning follows a judged clip, and a_vault's caged lamp is evidence a light *is* sometimes the mover you want.

DECISION: RENDER
WHY: The spec carries a bounded, authored-vigour mover that the committed 3072 still visibly depicts, the motion prompt derives correctly from that same spec, and no clip has been rendered yet — so the next step is the one render the pipeline allows.