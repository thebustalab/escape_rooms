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
| `auto_mask.py` | picks the post-processing mask threshold by OBJECT SOLIDITY, not by percentile. Also fills interior holes, which is what lets a high threshold and complete objects coexist |
| `paste_tile.py` | composites a repair tile back into a full-frame clip. Pastes the OBJECT (where the tile moved, intersected with `--region`), feathers, and colour-matches first |
| `colour_normalise.py` | flattens a global colour drift. **NOT a default step** — it can introduce visible brightness pumping; judge by eye, never by the number it optimises |

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
The existing 122 candidates in `rooms/wrangling/egypt/*/cine_*.mp4` are hotspot CROPS. Full-frame
metrics mean something different on them: `live%` is high by construction because the moving subject
fills the frame, and incoherence needs static architecture to compare against. Do not read those
numbers against these thresholds.
