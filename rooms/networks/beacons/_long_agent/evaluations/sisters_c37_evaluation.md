Checked the decision against the artefacts rather than the report.

**Verified independently:**

- **Prompt resolution.** `exp_art_prompt.py:89-104` does resolve spec-first — the `.txt` is the documented fallback. Running `scene_spec.render_motion_prompt` on the committed `authoring.sceneSpec` for `sisters` emits exactly the flag-line sentence ("The row of marker flags on their cord lifting and running along the line, the nearest ones snapping"). `col_cloud` carries `animate` but no `motion.phrase`, so it contributes nothing. The cloud-river `.txt` (dated Sep 9) is stale and display-only, as the worker said.
- **Provenance.** `rooms/networks/beacons/sisters/scene.png` committed 22:00, raw render 22:13 — the clip is from the fresh still.
- **Where the motion is.** My own per-tile temporal std over the raw 73-frame render: peak tile at **x=0.19, y=0.69**, 32x the frame-median tile; all tiles above 3x median confined to x∈[0.00,0.33], y∈[0.50,1.00]. Column profile is 10.4 at x≈0.15 and flat at 1.34–1.65 everywhere from x≥0.33 — including the `col_cloud` throat at x≈0.64. Bounded mover, old cloud river at the noise floor.
- **Content.** A crop of the mover region shows the cord between two iron stakes hung with faded red and bone-white flags, near and large in frame. It is the authored `marker_line`, not a blob or a camera artefact.
- **Precedent.** `notes/cinemagraph_ledger.md:1485-1486` records "a streaming pennant is a CYCLIC FLOW (return 0.03-0.05), and peak amplitude does not capture flow" — the exact signature here, not a fabricated comparison.

**Against the reject list:** no settings change; mover is bounded, not frame-filling; the 0.03 return is explicitly treated as ambiguous and drives a park-for-human-eye, not a re-author; no acceptance and no write into committed art or hotspots; no hand-written prompt; no AUTHOR_MOVER. The two side-observations (flags hanging slacker than the authored vigour; the stale `sisters.txt`) are flagged for a human, not proposed as loop actions.

Nothing left for the loop to fix on this clip.

VERDICT: PASS