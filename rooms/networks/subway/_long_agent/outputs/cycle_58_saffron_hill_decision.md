I have opened every strip at native resolution plus four targeted crops. Writing up.

FINDINGS: I opened all six native strips (`strip1..6_of6.png`) and then crops at x620–1180 (red unit's left end), x680–860 (that end face at 4×), x1400–1800 (black unit's near cab), x2020–2360 (black unit's far cab) and a 600 px seam-wrap. Checklist object by object: **the tea shelf** is present and excellent — strip 1, x≈150–500, plank shelf bolted to the tile with kettle, tea can, two enamel mugs and a folded newspaper at x≈900; **lampblack forward door** is present and well-formed — strip 4 / crop at x≈1470–1700, a proper cab with end window, a side door slid back on a lit interior with a seat and desk under a lamp; **lampblack rear door** is present — x≈2100–2300, the matching cab with its own open door on a lit interior, and the right tunnel mouth sits outboard beyond it; **madder forward door** is present and the best door in the frame — strip 3, x≈1030–1360, big cab windscreen, side door slid back on a warm lit interior. **The madder rear door is not depicted.** The red unit's left-hand end (x≈717–770) is a plain slab carriage end with a narrow gangway door and a small end window — no cab, no windscreen, no side door slid back on a lit interior — and the unit runs six-plus window bays back toward the tunnel rather than the two-or-three-bay double-ended unit the spec requires, so one of five hotspots has only a dim 40 px end door to box instead of a cab. The rest of the geometry is right: one continuous track bed crossing from the left tunnel mouth (x≈550–780) to the right (x≈2250–2450), both units down in the bed with wheels on the rails and floors level with a raised square platform edge, both mouths outboard, no flooding, no lettering (the tacked-up notices are squiggle-marks only). The seam is genuinely clean — plain saffron tile on both edges, with the tile courses, the conduit rail, the plinth and the floor joint all continuing across the join with no step or content crossing it. Secondary reservation: the whole frame is a single amber/sepia temperature, with none of the world plate's mandated cold blue-green, but that is not what I am gating on.

DECISION: REGENERATE
SPEC:
```json
{
 "room": "saffron_hill",
 "interior": true,
 "setting": "a cramped low barrel-roofed platform of a small underground station, tiled throughout in saffron yellow \u2014 the viewer is standing IN THE MIDDLE OF THE PLATFORM with the tiled platform wall at the viewer's back and THE SINGLE RUNNING ROAD CROSSING THE WHOLE VIEW FROM SIDE TO SIDE IN FRONT OF THE VIEWER, the curved roof coming down close on both sides, the whole space narrow and domestic and plainly worked in every day, orange crop growing thick across the side tile and over the brick soffits of the roof with a scraping trowel left leaning against the tiling; THE BORE RUNS STRAIGHT THROUGH FROM ONE TUNNEL MOUTH TO THE OTHER AND THERE IS NO BACK WALL, END WALL OR CROSS-WALL ANYWHERE IN THIS STATION",
 "seam": "a plain unbroken curve of saffron-yellow glazed tile running down to the platform edge, uniform and featureless",
 "seamOccluder": "a plain iron platform stanchion running floor to roof the full height of the frame",
 "elements": [
  {
   "id": "seam_left",
   "at": "on the far left",
   "desc": "a plain unbroken curve of saffron-yellow glazed tile running down to the platform edge, uniform and featureless, the left half of that one view"
  },
  {
   "id": "tunnel_mouth_left",
   "at": "to the left",
   "desc": "the left-hand end of the platform, where the sunken track bed and its rails duck into a black arched TUNNEL MOUTH \u2014 a brick-ringed opening set LOW, at track level below the platform, the rails carrying on into it and the dark swallowing them a few yards in, a cable run and a lamp bracket following them inside"
  },
  {
   "id": "kettle_shelf",
   "desc": "a plank shelf bolted to the tile at chest height carrying an electric kettle just come to the boil, a battered tea can, two enamel mugs and a folded newspaper",
   "label": "The tea shelf",
   "clue": true,
   "animate": {
    "motion": "steam rolling steadily up off the kettle and along under the low roof",
    "loop": "crossfade"
   },
   "at": "to the left"
  },
  {
   "id": "berth_madder_aft",
   "desc": "a short underground unit in flaking oxblood-red livery, the oldest stock on the network \u2014 flat tunnel-profile sides, dulled brass window frames and varnished beading, standing DOWN IN THE TRACK BED alongside the platform with its steel wheels ON the running rails and its floor level with the platform edge, a DRIVER'S CAB AT EACH END and both ends of it in view: this is its FAR cab at the LEFT-HAND end, its single large forward window facing away along the road and its side door slid back level with the platform edge on a lit interior",
   "label": "The madder train (red) \u2014 rear cab",
   "door": {
    "direction": "open",
    "to": "car_madder"
   },
   "at": "to the left of centre"
  },
  {
   "id": "berth_madder_fore",
   "desc": "the NEAR cab at the RIGHT-HAND end of that same short unit, identical to the far one and standing on the same rails in the same bed, its own single large forward window facing away along the road the opposite way and its own side door slid back level with the platform edge on a lit interior",
   "label": "The madder train (red) \u2014 forward cab",
   "door": {
    "direction": "open",
    "to": "car_madder"
   },
   "at": "just left of centre"
  },
  {
   "id": "berth_lampblack_fore",
   "desc": "a short heavy black iron works unit \u2014 flat soot-black sides, barred goods sections between its two cabs, standing DOWN IN THE TRACK BED alongside the platform on the SAME running rails as the red unit and just beyond it, with its steel wheels ON those rails and its floor level with the platform edge, a DRIVER'S CAB AT EACH END and both ends of it in view: this is its NEAR cab at the LEFT-HAND end, its single large forward window facing away along the road and its side door slid back level with the platform edge on a lit interior",
   "label": "The lampblack train (grey) \u2014 forward cab",
   "door": {
    "direction": "open",
    "to": "car_lampblack"
   },
   "at": "just right of centre"
  },
  {
   "id": "berth_lampblack_aft",
   "desc": "the FAR cab at the RIGHT-HAND end of that same short unit, identical to the near one and standing on the same rails in the same bed, its own forward window facing away along the road the opposite way and its own side door slid back level with the platform edge",
   "label": "The lampblack train (grey) \u2014 rear cab",
   "door": {
    "direction": "open",
    "to": "car_lampblack"
   },
   "at": "to the right of centre"
  },
  {
   "id": "tunnel_mouth_right",
   "at": "on the right, well BEYOND the far end of the black unit",
   "desc": "the right-hand end of the platform, where the same sunken track bed ducks into a second black arched TUNNEL MOUTH opposite the first, set equally low, its rails carrying on into the dark"
  },
  {
   "id": "seam_right",
   "at": "on the far right",
   "desc": "a plain unbroken curve of saffron-yellow glazed tile running down to the platform edge, uniform and featureless, the right half of that one view, joining its other half"
  }
 ],
 "atmosphere": "cramped, low, warm and domestic, saffron tile under a single string of work-lamps, damp haze, film grain. A CENTURY OF DERELICTION, ACTIVELY WORKED IN: crazed and missing glazed tile with the bedding mortar showing through, paint peeling in sheets, long rust and water stains bleeding down the walls, perished cable looped on old porcelain insulators, chipped enamel, sooted brick, treads worn hollow. And over the top of all of it the crew who work here now \u2014 notices, tally sheets, work rotas and curling postcards tacked and taped up, chalked marks and scratched tallies on the tile, duckboards laid over the wet, cable ties and gaffer tape, cheap bright LED work-lamps on yellow flex, a kettle, a coat on a hook. Lived-in, cared for, and plainly somebody's workplace. Warm, purposeful and characterful \u2014 a magnificent run-down place that a good crew has taken on and made theirs. NOT eerie, NOT spooky, NOT creepy, NOT haunted, NOT menacing, NOT post-apocalyptic and NOT an abandoned ruin: dark and dirty in places, and still plainly and warmly worked in. No cobwebs, no gloom-for-its-own-sake",
 "negatives": "This is an EQUIRECTANGULAR 360 panorama, not a flat photograph: the walls wrap continuously right around the viewer with strong barrel curvature, the ceiling and floor bow across the frame, and any surface toward the left or right of the frame is at the viewer's SIDE, seen at a glancing angle rather than face-on. NOT a flat frontal elevation of one wall, no single-vanishing-point composition, and never a view of the room from outside it or from across it. NEVER a long corridor or platform receding away from the viewer to a distant vanishing point, and NEVER an island platform with a road down each side: there is exactly ONE running road here and it crosses the frame HORIZONTALLY from side to side in front of the viewer, so the trains are seen broadside along their flanks and never end-on receding into the distance. No people, no lettering, no captions, no text, no signage, no readable writing of any kind, no station name anywhere, no daylight. No large blank empty wall areas anywhere \u2014 every surface carries the marks and clutter of a working place. There are EXACTLY 2 trains in this station and NO OTHERS \u2014 BOTH stand nose-to-nose on that ONE running road, the red unit filling the left-of-centre span and the black unit the right-of-centre span, and BOTH TUNNEL MOUTHS LIE OUTBOARD OF THEM, beyond the outer end of each unit, so neither unit reaches or enters a tunnel; do not add further trains, carriages or wagons anywhere in the frame or receding down any tunnel. Each is a SHORT double-ended underground unit, only two or three bays long, with a driver's cab at BOTH ends, and BOTH of its cabs are visible from where the viewer stands \u2014 never a long multi-bay carriage, and never a train whose far end is out of sight. Each reads as underground rolling stock \u2014 flat tunnel-profile sides, proper livery, cab windows \u2014 and never as a boxcar, goods wagon, crate, hut or isolated vehicle sitting by itself on the rails. No train runs away out of the frame into a tunnel. The platform and the running road are at DIFFERENT LEVELS: the platform is a raised walkway with a square edge, and the rails lie in a TRACK BED BELOW it, the ballast and sleepers dropping away roughly waist-deep at that edge. Every train stands DOWN IN that bed with its steel wheels ON the running rails, so its body rises above the platform and its floor comes level with the platform edge to step across. NEVER a train up on the platform paving, never one standing beside or across the rails, and never rails inlaid flush into a single flat floor like tramlines. The railway RUNS THROUGH this station and does not terminate in it: ONE continuous track bed crosses the whole width of the view from the left tunnel mouth to the right tunnel mouth in an unbroken line, never a short isolated pit under each train. The rails never simply stop, and they never run into a blank wall, a dead end, a buffer stop, a railing, a fence or a sealed arch \u2014 a train could enter from one mouth and leave by the other. The image is SHARP: no motion blur, no streaking, no smeared or doubled detail anywhere \u2014 everything in this picture is standing still, and any movement described is what the cinemagraph will add later, never something painted into the still. THE TRACKWAY IS NEVER FLOODED: wherever running rails appear they and their track bed are clear and usable, with no water standing over them, and there is no canal, waterway or navigable channel anywhere in the station \u2014 any water lies as shallow sheets or in a shallow drainage channel at the platform foot, never on the rails. Nothing eerie, spooky, creepy, haunted or menacing; no cobwebs, no horror atmosphere.",
 "continuity": []
}
```
WHY: The single change moves the red unit's full body description from `berth_madder_fore` onto `berth_madder_aft` so the unit is introduced at its first (leftmost) mention and its right-hand cab becomes the back-reference — mirroring the lampblack pair, which is ordered that way and rendered two proper cabs, whereas the madder pair back-referenced "that same short unit" before the unit existed in the prompt and rendered a single-cab six-bay carriage with a blank slab left end, leaving the `berth_madder_aft` hotspot nothing to box.