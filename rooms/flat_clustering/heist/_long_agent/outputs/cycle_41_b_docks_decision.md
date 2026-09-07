FINDINGS: I opened all six native-resolution strips (strip1–strip6) plus zoomed crops of the far-right arc (x 2280–2800 and 2320–2640, brightened ×4), the consignment board (x 1080–1420), the stair bay (x 1950–2600, brightened), and a side-by-side of the two wrap edges. Checklist object by object: **the clerk's terminal** is present and now correct — strip3, just right of the board, an upright hinged screen glowing pale green over a flat keyboard on the high desk, cables trailing, no legible text on the screen; the attempt-1 "anonymous metal tin" defect is fixed. **The consignment board** is present and well-formed in strip3, left of the desk — three ranks of hooked brass tallies over pigeonhole cards, generously sized and cleanly boxable, with no generated numerals. **The way back** (plank stair) is present at the strip4/strip5 boundary, treads and handrail well-formed, though it reads as rising *up* to a threshold onto the wharf rather than descending toward a yard. **On to the next call** is NOT DEPICTED: the far-right arc that should carry a door onto the gangway is a glazed bay with a bench and apparatus under it (x≈2330–2540), then a corner post, then roughly 500 px of unbroken tongue-and-groove to the right edge — there is no door leaf, no doorway, no gangway threshold anywhere right of the stair, so that hotspot has nothing to box. The cause is spec-level, not render luck: `on` sits in the "on the far right" slot, x=0.92, which is exactly the wrap-seam slot the room's own `seam` boarding claims, and the render resolved the conflict by making that whole arc seam wall. Tarp, hatch with crane gantry and wharf lamps, and the roped/straw-packed crates are all present and good; the seam itself is clean — plain boarding on both edges with continuous plank lines, no object crossing, only a mild tone step that is downstream-repairable. The room is otherwise handsome and atmospherically on-spec, but one of two doors is missing and that is a re-generation, not a morning fix.

DECISION: REGENERATE
SPEC:
```json
{
 "room": "b_docks",
 "setting": "the centre of a shipping agent's office above a working wharf in the small hours, consignment boards on every wall and a wide loading hatch standing open to the quay",
 "interior": true,
 "seam": "a plain stretch of varnished tongue-and-groove boarding, uniform and unbroken",
 "seamOccluder": "a timber roof-post running floor to ceiling",
 "elements": [
  {
   "id": "tarp",
   "at": "to the left",
   "desc": "a heavy canvas tarpaulin lashed at the open loading hatch, flapping and snapping in the wind off the water",
   "animate": {
    "motion": "the canvas tarpaulin flapping and snapping at the open hatch",
    "loop": "crossfade"
   }
  },
  {
   "id": "hatch",
   "at": "to the left",
   "desc": "the wide loading hatch itself, beyond it a crane gantry and black water under wharf lamps"
  },
  {
   "id": "board",
   "at": "just left of centre",
   "desc": "a consignment board of hooked brass tallies, each numbered within one narrow range",
   "clue": true,
   "label": "The consignment board"
  },
  {
   "id": "console",
   "at": "dead ahead in the centre",
   "desc": "a portable computer terminal open on the clerk's high desk, its hinged flat screen standing upright and glowing pale green over a worn keyboard laid flat on the desktop, cables trailing off the edge",
   "puzzle": true,
   "label": "The clerk's terminal"
  },
  {
   "id": "crates",
   "at": "just right of centre",
   "desc": "stencilled crates stacked and roped, one prised open and repacked with straw"
  },
  {
   "id": "back",
   "at": "just right of centre",
   "desc": "a plank stair back down toward the yard",
   "door": {
    "direction": "open",
    "to": "b_casino"
   },
   "label": "The way back"
  },
  {
   "id": "on",
   "at": "to the right",
   "desc": "a door onto the gangway out along the quay",
   "door": {
    "direction": "open",
    "to": "b_stateroom"
   },
   "label": "On to the next call"
  }
 ],
 "atmosphere": "the small hours, cold sodium off wet timber and black water, one warm desk lamp, salt haze, painterly, cinematic, film grain",
 "negatives": "No people, no figures, no crowds, no lettering, no captions, no text, no signage, no numbers.",
 "continuity": []
}
```
WHY: The single change is moving both doors one canonical slot inboard (`back` to "just right of centre", `on` to "to the right", vacating the x=0.92 far-right wrap slot entirely) so the `on` door no longer competes with the seam boarding for the same arc — which is why it rendered as blank plank wall and left the "On to the next call" hotspot with nothing to box.