# Cinemagraph tools

Built during the 2026-08-29/30 full-scene cinemagraph work. Rescued here from `/tmp/sweep`, which
does not survive a reboot.

**These operate on FULL-SCENE panorama cinemagraphs (3072x1024).** They are not calibrated for the
older hotspot-crop clips (288x512 and similar) — see the note at the end.

## Measurement

| tool | what it answers | notes |
|---|---|---|
| `loop_table.py` | how big is the loop jump, and is there a better cut point | returns the ABSOLUTE jump AND the ratio to the mean adjacent-frame step. **Report both** — they can move in opposite directions (see judgements). Also tabulates the best junction at each minimum loop length; validated by recovering the exact period of a 5x-repeated clip |
| `colour_drift.py` | does the scene warm/brighten across the clip | written after Lucas caught a 14.6-unit swing no other metric could see. Under ~2 is unnoticeable |
| `motion_mask.py` | per-pixel temporal std -> a motion map | `sample_frames()` derives its stride from the ACTUAL frame count; a fixed 73 silently sampled only the first third of a longer clip |

## Production

| tool | what it does |
|---|---|
| `bake_flat.py` | bakes a crossfade (and optionally a motion-mask composite) into a plain mp4 that loops anywhere with no viewer code |
| `make_boomerang.py` | builds forward+reverse `_boom.mp4` copies. The only loop mode that permits TRAVELLING motion |
| `add_to_viewer.py` | registers a clip in a 360 test viewer: copy, matching still, motion map, menu entry. Holds an exclusive lock across read-modify-write |
| `auto_register.py` | watches render folders and registers new clips as they land; skips renders that failed the frame-0 check |
| `sync_viewer.py` | rebuilds `cine360_endguide.html` from `cine360_test.html`, keeping its own clip list, so player changes never have to be made twice |
| `queue_drained.sh` | waits for ComfyUI's queue to be genuinely empty. Chaining on "the previous script exited" is wrong — a script that hits its poll timeout exits while its renders are still queued |
| `auto_mask.py` | picks the post-processing mask threshold by OBJECT SOLIDITY, not by percentile. Also fills interior holes, which is what lets a high threshold and complete objects coexist. `drop_small` is the SECOND axis — a region-size cut that removes isolated speckle a percentile can never see (default off) |
| `paste_tile.py` | composites a repair tile back into a full-frame clip. Pastes the OBJECT (where the tile moved, intersected with `--region`), feathers, and colour-matches first |
| `colour_normalise.py` | flattens a global colour drift. **NOT a default step** — it can introduce visible brightness pumping; judge by eye, never by the number it optimises |

## Unattended repair (the overnight loop)

| tool | what it does |
|---|---|
| `cine_judge.py` | judges ONE **baked** clip — the file that ships — and says which tier would fix it (`rebake` / `rerender` / `human`). Files the verdict at `cine_<state>.judge.json`. **Never returns an approval:** the verdicts are `reject` and `hold`, where hold means "survived the gates, needs your eye" |
| `cine_iterate.py` | the deterministic half of the loop: scope discovery (specced AND spec-less states), spec validation and writing, the no-GPU rebake, the detached re-render and its status file. No AI in it |
| `_iterate_render.py` | renders one (room, state) detached and writes a machine-readable status file. Launched by `cine_iterate`, not by hand |
| `cine_overnight.py` | surveys the collection and creates one `cine_iterate` long_agent job per scenario, queued into the overnight observer. `--survey` changes nothing |
| `test_cine_judge.py` | pins the two verdicts the judge got WRONG in its first draft (see below) |

The decision-making half is the `cine_iterate` long_agent task
(`Utilities/long_agent/tasks/cine_iterate.yaml` + `run_cine_iterate_cycle`). Operating instructions
live in the `escape_room_motion` skill.

### Two things `cine_judge.py` found on clips that had already shipped
- **The mask silently discarding authored motion.** A subject the spec names as moving, which the
  mask pins still, shows a frozen source frame in the bake. `emporion/base` trough_water renders at
  p95 **19.73** and bakes to **exactly 0.00**; `market_price/base` side_awnings 9.83 -> 0.00. Nothing
  had ever measured named subjects on the baked file. Fixed by a rebake, not a re-render.
- **A breathing room.** `hold/base`'s hanging lamp all but goes out over the loop and the whole hold
  dims with it — background swing 6.07 against a clean group of <=1.29.

### Stale art is handled WITHOUT a diagnosis cycle
A clip fails the frame-0 gate for two very different reasons, and one of them needs no thinking at
all: **the still was recommitted after the clip was baked**, so the clip is a perfectly good
animation of superseded art. `is_stale()` settles it from two signals that must BOTH agree — the
still's mtime is newer AND frame 0 no longer correlates with it. Either alone is wrong: mtime alone
fires on a `touch` or a checkout and spends ten minutes of DGX on unchanged art; correlation alone
cannot tell replaced art from a noise render.

When that is a clip's ONLY fault (`stale_only_reject`), the loop re-renders it directly — no worker,
no evaluator, no frames opened. It was worth building: on the first beacons night every one of the
25 clips was stale (stills recommitted 09-03 over clips baked 09-02, `anvil/base` correlating 0.02),
and the loop spent a full diagnosis pair re-deriving the same answer six times with 18 more queued.
A stale sweep over the whole scenario now costs 86 s.

### Two traps the judge itself fell into
- **`repair_list` is not "dead".** It deliberately includes every `force_repair` subject, because
  that flag is Lucas's standing instruction to repair something he judged too quiet. Read as
  deadness it gave **fourteen false deaths against eight real ones** on the egypt set.
- **Background swing must not gate.** The daytime separation is decisive and the NIGHT states
  destroy it: `quay/night` swings 4.94 and is fine against `hold/base` 6.07 which is not, and
  normalising for darkness inverts the ordering (quay/night 32.9% vs hold 28.4%). Report-only, like
  colour drift and incoherence, and for the same reason.

## Traps that cost real time here
- **`cg.poll()` gives up at 900 s.** A long render exceeds that and reports TIMEOUT while succeeding.
  A timeout means "check `/history`" — and note that `/history` reporting `success` only means the
  graph ran; two clips of pure noise were filed as successes.
- **Copying a sweep script?** Change its `filename_prefix` AND its upload names. Sharing either with
  a sibling silently mixes results between stages.
- **Fixed scratch directories** break under concurrency. Use `tempfile.mkdtemp`.
- **Metrics on a masked composite must be measured inside the video region.** Averaging over the
  whole frame includes the static still, which dilutes drift toward zero and hides it.

## `z_sweeps/`
The 36 experiment scripts, kept as the record. Each one's docstring states what it tested and why,
including the ones that failed. Results are in `../notes/cinemagraph_judgements.md`.

## Not calibrated for hotspot clips
Full-frame metrics mean something different on a hotspot CROP: `live%` is high by construction because
the moving subject fills the frame, and incoherence needs static architecture to compare against. Do
not read a crop's numbers against these thresholds.

**Where the crops actually are (corrected 2026-09-05).** This section used to point at
`rooms/wrangling/egypt/*/cine_*.mp4` and call those 122 files hotspot crops. That is no longer true and
following it now gets you the wrong answer: the boxed-era candidates were purged on 2026-09-02 and the
54 clips at that path today are all 3072x1024 full-scene panoramas, which these thresholds DO apply to
and which `cine_judge.py` measures on every run. The surviving crops sit in
`rooms/wrangling/egypt/_scratch/orphaned_media/`.
