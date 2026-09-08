FINDINGS: I opened all six native-resolution strips (strip1–strip6 of 6) plus three close crops at x1500–2100, x2000–2700 and x400–1100. The cutting bench is DEPICTED and well-formed — strip 3, x≈1000–1500: long steel bench, hard work-lamp on a stalk, curved blades, scales, shallow trays, kit on the shelf below; the ceiling extractor fan is also there, strips 3–4 at x≈1450–1650. Everything else on the checklist fails. The weld (yellow) unit is not a short double-ended unit: the crop at x400–1100 shows a single-ended narrow-gauge loco with its cab window facing the VIEWER, a low deck running away from it into the left tunnel, and a separate yellow tipper wagon of flats beside it — there is no second identical cab, so the "rear door" hotspot has nothing to box. The lampblack (grey) unit is the same failure at x2000–2700: one black loco cab facing the viewer with a rake of open barred goods wagons trailing away out of the frame into the right-hand tunnel, no far cab, so its rear door has nothing to box either — and those open wagons are exactly the "goods wagon" reading the negatives forbid. Train count is broken: a second, distinct yellow loco sits at x≈1700 (crop x1500–2100) at the head of the black rake, so the frame carries three locos and multiple wagons instead of EXACTLY 2 units. The room's core geometry is absent — there is no raised platform and no sunken track bed anywhere; the rails are inlaid flush into one flat paved floor like tramlines and every vehicle stands on the paving, several of them beside rather than on the rails, all three explicitly forbidden. Both tunnel mouths are present (strip 1 right, strip 5–6) and the track runs through rather than terminating, no flooding, no readable lettering (the tacked-up notices are unreadable scribble), and the seam is actually the best thing here: strip 6's right edge and strip 1's left edge are both the plain riveted works-grey screen wall at matching tone and rivet pitch, with only flush rails crossing the join.

DECISION: REGENERATE
SPEC:
```json
{
 "room": "cropping_yard",
 "interior": true,
 "setting": "the platform of a disused underground station, worked now as the works' cutting floor — the viewer is standing IN THE MIDDLE OF THAT PLATFORM, which is a RAISED WALKWAY with a square worn granite edge, broad and low and businesslike, with the running rails lying in a SUNKEN TRACK BED roughly WAIST-DEEP BELOW that edge, waist-high stacks of banded flats waiting for a car up to the racks",
 "seam": "a plain riveted sheet-steel screen wall painted works grey, uniform and unbroken",
 "seamOccluder": "a galvanised racking upright running floor to ceiling the full height of the frame",
 "elements": [
  {
   "id": "seam_left",
   "at": "on the far left",
   "desc": "a plain riveted sheet-steel screen wall painted works grey, uniform and unbroken, the left half of that one view"
  },
  {
   "id": "tunnel_mouth_left",
   "at": "to the left",
   "desc": "the left-hand end of the platform, where the sunken track bed and its rails duck into a black arched TUNNEL MOUTH — a brick-ringed opening set LOW, at track level below the platform, the rails carrying on into it and the dark swallowing them a few yards in, a cable run and a lamp bracket following them inside"
  },
  {
   "id": "extractor",
   "desc": "a big slow ducted extractor fan set in the ceiling, its blades turning steadily, drawing a thin haze of lichen dust up out of the room",
   "animate": {
    "motion": "the extractor blades turning steadily and the dust haze drawing up into them",
    "loop": "crossfade"
   },
   "at": "to the left"
  },
  {
   "id": "cutting_bench",
   "desc": "a long steel cutting bench under a hard work-lamp, laid with curved blades, a set of scales and shallow trays of cut orange crust waiting to be flatted",
   "label": "The cutting bench",
   "clue": true,
   "at": "just left of centre"
  },
  {
   "id": "berth_weld_fore",
   "desc": "a short ochre-yellow works unit — a driver's cab at each end with an open flatbed deck between them, drop gates at knee height, stacked flats lashed down under canvas straps, standing DOWN IN THE TRACK BED alongside the platform with its steel wheels ON the running rails and its floor level with the platform edge, a DRIVER'S CAB AT EACH END and both ends of it in view: this is its NEAR cab, its single large forward window facing away down the tunnel and its side door slid back level with the platform edge on a lit interior",
   "label": "The weld train (yellow) — forward cab",
   "door": {
    "direction": "open",
    "to": "car_weld"
   },
   "at": "dead ahead in the centre"
  },
  {
   "id": "berth_weld_aft",
   "desc": "the FAR cab at the other end of that same short unit, identical to the near one and standing on the same rails in the same bed, its own forward window facing away down the tunnel the opposite way and its own side door slid back level with the platform edge",
   "label": "The weld train (yellow) — rear cab",
   "door": {
    "direction": "open",
    "to": "car_weld"
   },
   "at": "just right of centre"
  },
  {
   "id": "tunnel_mouth_right",
   "at": "to the right",
   "desc": "the right-hand end of the platform, where the same sunken track bed ducks into a second black arched TUNNEL MOUTH opposite the first, set equally low, its rails carrying on into the dark"
  },
  {
   "id": "berth_lampblack_fore",
   "desc": "a short heavy black iron works unit — flat soot-black sides, barred goods sections between its two cabs, standing DOWN IN THE TRACK BED alongside the platform with its steel wheels ON the running rails and its floor level with the platform edge, a DRIVER'S CAB AT EACH END and both ends of it in view: this is its NEAR cab, its single large forward window facing away down the tunnel and its side door slid back level with the platform edge on a lit interior",
   "label": "The lampblack train (grey) — forward cab",
   "door": {
    "direction": "open",
    "to": "car_lampblack"
   },
   "at": "to the right"
  },
  {
   "id": "berth_lampblack_aft",
   "desc": "the FAR cab at the other end of that same short unit, identical to the near one and standing on the same rails in the same bed, its own forward window facing away down the tunnel the opposite way and its own side door slid back level with the platform edge",
   "label": "The lampblack train (grey) — rear cab",
   "door": {
    "direction": "open",
    "to": "car_lampblack"
   },
   "at": "on the far right"
  },
  {
   "id": "seam_right",
   "at": "on the far right",
   "desc": "a plain riveted sheet-steel screen wall painted works grey, uniform and unbroken, the right half of that one view, joining its other half"
  }
 ],
 "atmosphere": "broad, low, hard-lit and businesslike, works grey and galvanised steel against the orange of the crop, dust haze, film grain. A CENTURY OF DERELICTION, ACTIVELY WORKED IN: crazed and missing glazed tile with the bedding mortar showing through, paint peeling in sheets, long rust and water stains bleeding down the walls, perished cable looped on old porcelain insulators, chipped enamel, sooted brick, treads worn hollow. And over the top of all of it the crew who work here now — notices, tally sheets, work rotas and curling postcards tacked and taped up, chalked marks and scratched tallies on the tile, duckboards laid over the wet, cable ties and gaffer tape, cheap bright LED work-lamps on yellow flex, a kettle, a coat on a hook. Lived-in, cared for, and plainly somebody's workplace. Warm, purposeful and characterful — a magnificent run-down place that a good crew has taken on and made theirs. NOT eerie, NOT spooky, NOT creepy, NOT haunted, NOT menacing, NOT post-apocalyptic and NOT an abandoned ruin: dark and dirty in places, and still plainly and warmly worked in. No cobwebs, no gloom-for-its-own-sake",
 "negatives": "This is an EQUIRECTANGULAR 360 panorama, not a flat photograph: the walls wrap continuously right around the viewer with strong barrel curvature, the ceiling and floor bow across the frame, and any surface toward the left or right of the frame is at the viewer's SIDE, seen at a glancing angle rather than face-on. NOT a flat frontal elevation of one wall, no single-vanishing-point composition, and never a view of the room from outside it or from across it. No people, no lettering, no captions, no text, no signage, no readable writing of any kind, no station name anywhere, no daylight. No large blank empty wall areas anywhere — every surface carries the marks and clutter of a working place. There are EXACTLY 2 trains in this station, one at each platform face and NO OTHERS — do not add further trains, carriages or wagons anywhere in the frame or receding down any tunnel. Each is a SHORT double-ended underground unit with a driver's cab at BOTH ends, and BOTH of its cabs are visible from where the viewer stands. Each reads as underground rolling stock — flat tunnel-profile sides, proper livery, cab windows — and never as a boxcar, goods wagon, crate, hut or isolated vehicle sitting by itself on the rails. No train runs away out of the frame into a tunnel. The platform and the running road are at DIFFERENT LEVELS: the platform is a raised walkway with a square edge, and the rails lie in a TRACK BED BELOW it, the ballast and sleepers dropping away roughly waist-deep at that edge. Every train stands DOWN IN that bed with its steel wheels ON the running rails, so its body rises above the platform and its floor comes level with the platform edge to step across. NEVER a train up on the platform paving, never one standing beside or across the rails, and never rails inlaid flush into a single flat floor like tramlines. The railway RUNS THROUGH this station and does not terminate in it: the track crosses the whole view and disappears into an arched tunnel mouth at EACH end of the platform. The rails never simply stop, and they never run into a blank wall, a dead end, a buffer stop or a sealed arch — a train could enter from one mouth and leave by the other. The image is SHARP: no motion blur, no streaking, no smeared or doubled detail anywhere — everything in this picture is standing still, and any movement described is what the cinemagraph will add later, never something painted into the still. THE TRACKWAY IS NEVER FLOODED: wherever running rails appear they and their track bed are clear and usable, with no water standing over them, and there is no canal, waterway or navigable channel anywhere in the station — any water lies as shallow sheets or in a shallow drainage channel at the platform foot, never on the rails. Nothing eerie, spooky, creepy, haunted or menacing; no cobwebs, no horror atmosphere.",
 "continuity": []
}
```
WHY: The one change is the `setting`, which literally commissioned "a wide flat working floor built out over the rails" and so instructed the flat single-level paved floor with flush tramlines that the negatives forbid — the render obeyed the setting, giving no raised platform, no waist-deep track bed, and locos and open goods wagons standing on the paving instead of two double-ended units down in the bed.