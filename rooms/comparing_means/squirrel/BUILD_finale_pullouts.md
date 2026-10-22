---
authority: intent
---

# Build spec: Seedfall's two lever finales, using the single-reference pull-out (2026-10-22)

**Goal.** Each of Seedfall's two `endsEscape` levers (`lo_lantern/the_lantern_lever`, `up_lamp/the_lamp_lever`) plays a
pull-out `transit`. The camera starts on the room with its light just lit, pulls out of it, and rises to one shared high
aerial of the whole snowy city at night with BOTH lights lit. The escape-done card opens over the last frame. Design:
`notes.md` → *Finale (Lucas, 2026-10-21)*. Neither lever has a `transit` yet (checked 2026-10-22).

**Why redo it.** The existing test (`_scratch/finale/transit_upper/`, chained `exp_travel` waypoints, Lucas: "not bad,
not perfect") uses the recipe that failed on spa: it pushes in, stalls, then smears. Spa's finale was rebuilt with ONE
block-model reference and ONE Cameraman render, and Lucas accepted it ("that's the one"). **Read the method first:**
`.claude/skills/escape_room_motion/SKILL.md` → *Escape pull-outs — ONE render, ONE block reference for the whole move*.
The worked example is `../spa/_scratch/finale/` (`block/block_pullout.py`, `block/run_block_v3.sh`, `gen.sh`,
`prompt_bridge.txt`).

## What already exists (`_scratch/finale/`)

- `lit_up_lamp_1/2.png` and `lit_lo_lantern_1/2.png`: unmasked edits of each committed `scene.png` with the light lit.
- `halfway_upper_1/2.png` and `halfway_lower_1/2.png`: exterior views of each light from the air (generated independently).
- `city_aerial_1/2.png`: the shared final aerial.
- `transit_upper/`: the old chained test (`w0..w3`, `meta.json` rolls, `run.sh`).
- **Which draws Lucas prefers is not recorded.** Ask him, or show him the pairs side by side.

## Steps

1. **Pick the stills with Lucas** (one lit room per lever, one halfway each, one shared aerial). Put the previews in
   `temp/mobile_previews/seedfall_finale/` and send them as Tools-relative paths.
2. **Make the halfway → aerial continuity hold.** Spa rule 5: the final frame must share the guide still's sky and light,
   or the move has no visible connection. Spa solved it by making the final still an EDIT of halfway, pulled back. Here
   the aerial is SHARED by both levers, so go the other way: **derive each halfway as an edit OF the chosen aerial**
   ("same moment, camera much closer to the lighthouse / harbour lantern, level with it"). Then both pull-outs end on the
   identical aerial and each halfway carries its sky. Show Lucas the derived halfways before rendering.
3. **Build one block model per lever** (copy `../spa/_scratch/finale/block/block_pullout.py`): the lamp room (glazing
   bars, lens, rail) or the lantern landing, the lighthouse on its point or the harbour bastion and mole, and the cliff
   city with texture. Shape the path so the camera passes the halfway pose near the guide frame. **Place the camera by
   comparing `--still N` frames at 768×256 against the real stills** (start, guide frame, end), not by real-world scale.
   The generated world is small (spa's halfway was ~14 m from its tower).
4. **Rolls.** Spa's stills had the subject at x = 0.5, so `rollFrom` was 0. Check where each lit room's light and lever
   sit. If the light is not centred, roll the start still so it is (henges `make_frames.py`; shift = 1536 − centre px),
   record `rollFrom` = shift × 360 / 3072, and roll the block start heading to match. The aerial was rolled −126.3° in
   the old test: re-measure for the new pipeline.
5. **Render** (copy `run_block_v3.sh`): reference at 768×256 → upscale to 1536×512; one Cameraman `exp_travel` per lever
   (`--a` lit room, `--b` aerial, `--guide halfway@<frame>:0.5`, `--length 145 --seed 7 --a-strength 0.6 --size
   1536x512`, `--ic-lora` Cameraman); upscale to 3072×1024; `clip_motion_map.py`; previews and maps to
   `temp/mobile_previews/seedfall_finale/`. Run detached (`setsid nohup bash -lic …`).
6. **Review before Lucas sees it:** ten frames across each clip. Watch for a push-in at the start, a hold, smearing, or
   anything flipping between frames. Send each clip WITH its motion map.
7. **Wire on his yes:** copy each clip into its room folder (e.g. `up_lamp/transit_finale.mp4`) and set
   `transit: {video, rollFrom, rollTo: 0, sfx?, sfxVolume?}` on the PLACED lever only. **Check first whether
   `_scratch/build_scenario.py` regenerates `scenario.json`** (Seedfall is builder-driven): if so, the wiring must live in
   the builder or survive a rebuild. Then run `authoring_v2/preflight.py comparing_means/squirrel`,
   `validate_assets.py`, `test_squirrel.py` and `node --test tests/*.test.js tests/*.test.mjs`.
8. **Record** the result in `notes.md` (overwrite the *Finale* bullet's state, don't append a status block). If anything
   new was learned, extend the skill's *Escape pull-outs* section.

## Acceptance

- Each clip is one continuous move: room → out → up → the shared aerial, with no cut, push-in, stall or flipping detail.
- Both clips end on the identical aerial frame.
- Lucas has said yes to each clip. Nothing is accepted by an agent.
- Preflight, validate_assets, `test_squirrel.py` and the node suite are green after wiring.
