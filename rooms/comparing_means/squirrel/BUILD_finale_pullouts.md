---
authority: intent
---

# Build spec: Seedfall lever pull-outs, v2 (2026-10-22)

**Goal.** Each of Seedfall's two `endsEscape` levers (`lo_lantern/the_lantern_lever`, `up_lamp/the_lamp_lever`) plays a
flat pull-out `transit`. The lit light is centred and the camera pulls back from inside the room to ONE shared night
aerial of the snowy city with both lights lit. The escape-done card opens over the last frame.

**Where things stand.** v1 of both clips is rendered and **approved by Lucas** ("both good"), but **not yet wired**:
`_scratch/finale/block/finale_upper.mp4` and `finale_lower.mp4` (3072×1024, with `_map.png` motion maps). Lucas asked for
a **v2 made by following the written recipe**: `.claude/skills/escape_room_motion/SKILL.md` → *Escape pull-outs* (rules
1-8 from spa; rules 9-13 "Two levers, one shared aerial" from this build). v1 stays as the accepted fallback. **Never
overwrite a v1 file**; name every v2 output `*_v2*`.

**What v2 should change is not recorded.** Ask Lucas first, in one line: is v2 a clean re-run of the recipe (a test
that it is complete), or does he want something different from v1, such as a new aerial, a different move or timing?
If he just says "follow the recipe", treat it as a re-run: keep the settled stills below, rebuild everything after them,
and note every place the recipe was unclear or wrong.

## Settled stills (Lucas, 2026-10-22). Reuse them unless he says otherwise. All in `_scratch/finale/`

- Lit rooms: `lit_up_lamp_2.png` and `lit_lo_lantern_1.png` (one unmasked edit of each committed `scene.png`).
- Shared aerial: `city_aerial_v2_2.png` (prompt `prompt_city_aerial_v2.txt`, `gen_aerial_v2.sh`).
- Aerial rolled so each light is centred: `aerial_v2_rolled_upper.png` (−1021 px, −119.65°) and
  `aerial_v2_rolled_lower.png` (+989 px, +115.9°).
- Halfways = crops of the rolled aerial, sharpened (`gen_crop.sh`, `prompt_crop_sharpen.txt`; crop 1620×540 at y0 170
  upper / 250 lower). Lucas: "any of those will work". v1 used `crop_halfway_upper_2.png` and `crop_halfway_lower_1.png`.
- v1's exact render inputs: `_scratch/finale/transit_v2/` (`a_*`, `b_*`, `guide_*`; the lantern still is rolled −44 px
  so the lantern is centred, giving `rollFrom` ≈ −5.2°).

## Steps

1. Ask Lucas what v2 changes (above). Record his answer in `notes.md` → the *Finale* bullet (overwrite, don't append).
2. Read the recipe (skill rules 1-13) and v1's scripts: `_scratch/finale/block/block_pullout.py` (`--lever upper|lower`),
   `block/compare.py`, `block/run_block.sh`. Copy them to `*_v2` names; don't edit v1's in place.
3. If the stills change, regenerate only what changes, following rules 10-11 (pin the aerial to the front half, crop
   the halfways from it). Show Lucas new stills as pick sheets in `temp/mobile_previews/seedfall_finale/` before
   rendering anything.
4. Block model per lever: render `--still 0 / 68 / 144` and compare with `compare.py` (room, halfway, aerial beside the
   block) until the layout and horizon roughly match (rule 12).
5. Render detached (`setsid nohup bash -lic "<script>"`), one lever after the other, writing `finale_<lever>_v2.mp4` +
   map + previews.
6. **Review before Lucas sees anything:** ten frames across each clip. Look for a push-in at the start, a hold,
   smearing, or details flipping, especially where the camera leaves the lamp room's glass (the room's city is mirrored
   against the aerial's). v1 skipped this check; don't.
7. Send each clip WITH its motion map, v1 beside v2. Lucas picks.
8. **Wire the chosen version on his yes:** copy the clip into the room folder (`up_lamp/transit_finale.mp4`,
   `lo_lantern/transit_finale.mp4`). Then set `transit: {video, flat: true, rollFrom}` (rollFrom 0 upper, −5.2 lower
   for v1's inputs) on the PLACED lever hotspot, through `authoring_v2/scenario_lock.update_json`. Back up
   `scenario.json` to `z_archive/` first (cp to /tmp, then a bare `mv`). First check whether
   `_scratch/build_scenario.py` would overwrite it: `merge_existing()` keeps committed hotspots, but confirm. Then
   run `authoring_v2/preflight.py comparing_means/squirrel`, `validate_assets.py`, `test_squirrel.py` and
   `node --test tests/*.test.js tests/*.test.mjs`.
9. Fix the recipe wherever v2 found it unclear or wrong: edit the skill section in place, deleting the superseded
   rule.

## Acceptance

- Each clip is one continuous move, played flat: the lit light is centred, the camera pulls out and up to the shared
  aerial, with no cut, push-in, stall, smear or flipping.
- Both clips end on the same aerial (rolled differently per lever is fine).
- Lucas has picked v1 or v2 for each lever and said yes; nothing is accepted by an agent.
- After wiring, preflight, validate_assets, `test_squirrel.py` and the node suite are green.
