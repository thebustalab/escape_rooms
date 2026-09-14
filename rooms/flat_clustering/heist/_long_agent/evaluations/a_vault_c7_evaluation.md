I checked the worker's claims against the code and the frames rather than taking them on trust.

**The mislabel is real, and it's a runner bug.** At Utilities/long_agent/long_agent.py:3638 the room loop calls cine_room's gate() directly and then does `findings["auto_rejected"] = "camera gate"` unconditionally on any failure — it clobbers whatever actually fired. cine_room.py itself only ever writes the long "glitch gate: transient breadth…" string, and a camera rejection needs camera == "CAMERA MOVES". So `camera: "still"` plus `"camera gate"` is exactly the impossible pair the worker described, and the cause is the runner, not the gate. The same shortcut explains the missing re-roll: the loop calls gate() rather than cine_room's main(), so the sanctioned two-seed roll never executes and no `rolls` key appears.

**The real fire is the glitch gate** — breadth 0.896 against the 0.667 threshold wired today.

**The frames back the false-positive hypothesis.** I pulled frames 0, 20, 41 and 72 from the raw render. The clip starts dark, ramps to a very bright frame around the 57% mark, and comes back down — a whole-frame illumination swing with the caged lamp visibly shifted. Geometry in the box wall, the vault door and the steps holds steady across all four; nothing is smearing or tearing. So what the breadth metric is reading as "transient distortion" is, on the frames I can see, a global brightness pump from the light sweep. Whether that reads as beautiful or as a strobe is a judgement only Lucas's eye settles — which is precisely what PARK is for.

**Against the reject list:** no settings lever, no frame-filling mover, no zero-return reasoning (return is 0.77 and the worker argues the clip is alive, not dead), no acceptance and no write into scenario.json, no hand-written prompt, no AUTHOR_MOVER. PARK is in ROOM_DECISIONS and its only side effects are setting `parked` and notifying the human — safe and reversible.

Halting here is the right call: with every gate rejection currently mislabelled, letting the chain run sends each future cycle down the wrong remedy branch.

VERDICT: PASS