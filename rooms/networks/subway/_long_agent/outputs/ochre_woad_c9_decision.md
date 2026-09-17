I read the four evidence files, then checked this room's actual state on disk.

**What I found**

- `lamp_on_flex` already carries a full `motion` block — `moves: true`, an authored `vigour` ("swinging gently on its flex, its light swinging with it") and a phrase. So the spec declares a bounded mover with its amount set at authoring time.
- The motion prompt reported as NONE is only the absence of the `.txt` fallback. Rendering from the spec gives a clean 30-word house-form prompt: *"locked-off static camera, zero camera movement. The caged lamp swinging very slowly on its flex, barely moving. Only that moves; everything else stays perfectly still. Seamless natural loop."*
- `scene.png` was regenerated today at 14:30 from the current spec (the round-3 tunnel-mouth fix), and it depicts the mover: a single caged lamp on a long yellow flex hanging free from the vault just right of centre, small, isolated, nothing like frame-filling. A lamp is in the confirmed-mover list. The round-3 fault is also gone — exactly one tunnel mouth, the stair well inboard of the edge.
- `art_generated: 1`, no `cine_cand/ochre_woad`, gate report empty, nothing tried. No clip has ever been rendered against this art.

Spec, still and prompt all agree, and the only missing thing is the render itself. Nothing here calls for re-authoring — the a_vault precedent says a swinging lamp's brightness swing can lift the raw glitch reading, but the gate requires both readings over 0.70 and a_vault cleared it, so that's the gate's business, not the art's.

DECISION: RENDER
WHY: The spec already declares one bounded mover with authored vigour, the freshly committed still plainly depicts that caged lamp on its flex, the motion prompt resolves cleanly from the spec, and no clip exists yet — so the single default render at 3072x1024, end guide 0.70, is the next step.