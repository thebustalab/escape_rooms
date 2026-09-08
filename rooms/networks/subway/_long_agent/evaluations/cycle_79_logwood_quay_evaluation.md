I opened the candidate myself and cut my own native-resolution crops rather than reusing the worker's.

**Verification of the worker's central claim:** confirmed. My crop at x900–1600 shows the blue unit's underframe meeting the wet flagstones directly — no wheels, no rails, no ballast, no platform lip; the paving runs continuously under it. My crop at x1500–2200 shows the same for the green unit. The x2100–2850 crop shows the green cab sitting on the paving with the tunnel's rails running diagonally *past* it at near-platform level — precisely the "standing beside rails it is not on" negative. The sump pump (logbook and pencil on the casing, yellow hose to the channel) and all four car doors on lit brass interiors are present and boxable, as claimed.

**Spec check:** I diffed the proposed JSON against `scenario.json` (`rooms[6].authoring.sceneSpec`). It is byte-identical except for one inserted first element, `platform_edge` — setting, seam, seamOccluder, all ten prior elements, atmosphere and negatives are unchanged. All five checklist objects survive, and this is a genuinely new lever: `notes.md:1966–1980` records that the TRACKBED clause was already pushed into `setting`, `negatives` and every berth desc, and this render proves that prose placement does not take.

Grounded, single-variable, non-repeating, no object dropped, real named defect — and no commit is at stake since nothing is committed yet.

VERDICT: PASS