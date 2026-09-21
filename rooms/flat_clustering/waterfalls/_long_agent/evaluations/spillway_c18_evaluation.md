**Verdict: pass.** The worker's RENDER call breaks none of the rejection rules, and I checked the still and the spec myself.

- **The still matches the spec.** `spillway/scene.png` (3072×1024, updated at 12:51) shows:
  - four square mouths on the left, each gushing into one floor channel that runs out to a grated drain;
  - exactly one free-falling stream, dropping from a roof slot straight through the floor hatch, with the ladder rungs behind it;
  - the rope bridge through the central arch, dry and tied at both ends;
  - the rotted grilles to the right of centre and the scored tally pillar on the right.
  
  The light is green-white only, with no warm colour anywhere.
- **Both movers are bounded.** The ropes of water are confined to the left rank of mouths and their channel, and the stream is confined to the hatch column. Neither fills the frame, and each has its vigour written into the spec.
- **No clip exists for this still.** The only earlier render, `ri28`, was made from the archived daylight base. That means this isn't an AUTHOR_MOVER on something never rendered, and there's no zero return being misread.
- **No settings change, no accept, no writes into scenario.json, no hand-written art prompt.** The motion prompt comes from the spec through `render_motion_prompt`, and the render runs once at the defaults.

VERDICT: PASS