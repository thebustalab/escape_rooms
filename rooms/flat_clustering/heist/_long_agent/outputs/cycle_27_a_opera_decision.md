FINDINGS: I opened all six native-resolution strips (strip1–strip6) plus enlarged crops of the lighter (x1560–1760), the right-hand door cluster (x2020–2320), the left-rear panelling (x830–1120), and the stage (x1490–1690). Checklist: the **writing-slope terminal** is present and well-formed — a leather slope on the box rail with an open dark portable terminal, dead ahead at x≈1450–1640, straddling strips 3/4; **the way back** is present at x≈2130–2260 as a crimson-curtained doorway in a gilt frame against a dark panel; **on to the next call** is present at x≈2250–2400 as a second curtained aperture opening onto a lamplit arch and red-carpeted grand stair, correctly ordered to the right of the first, though the two abut with only a narrow mullion between them; **the monogrammed lighter** is present at x≈1600–1700 on the velvet seat but is the defect — it renders as a flat cigarette-case slab about 110×90 px lying in deep shadow, its "marque" a smudged cluster of gilt dots roughly 25×15 px with a smeared engraved band beneath that reads as pseudo-lettering, so the one token whose entire pedagogical job is to be the *legible* mark that calibrates the other four ambiguous ones is itself illegible. Core concept holds: the box genuinely overhangs the auditorium, tiers drop away, and the stage is a single small brilliant source far below. The seam is excellent — both edges are plain crimson flock, mean RGB (48.5, 16.5, 13.4) left versus (49.7, 15.6, 12.5) right, a delta of ~1 per channel with matching texture variance and no object crossing the join. Decisively, I checked `scene_specs_heist.json` on disk: the lighter's desc is still the *original* "left on the velvet seat, its house marque crisp and unmistakable" — attempt 1's proposed rewording was never applied, so this is a second roll of unchanged wording, not a failure of the fix.

DECISION: REGENERATE
SPEC:
```json
{
 "room": "a_opera",
 "setting": "the centre of a gilded private box overhanging a great opera auditorium mid-performance, the tiers and the lit stage falling away beyond the parapet",
 "interior": true,
 "seam": "a plain stretch of deep crimson flock wallpaper, uniform and unbroken",
 "seamOccluder": "a fluted gilt pilaster running floor to ceiling",
 "elements": [
  {
   "id": "swag",
   "at": "to the left",
   "desc": "a heavy crimson velvet swag curtain gathered at the box mouth, stirring in a draught from the flies",
   "animate": {
    "motion": "the heavy velvet swag curtain breathing slowly in the draught",
    "loop": "boomerang"
   }
  },
  {
   "id": "parapet",
   "at": "just left of centre",
   "desc": "the box parapet in worn gilt, and beyond it the auditorium tiers dropping away to a small brilliantly lit stage"
  },
  {
   "id": "console",
   "at": "dead ahead in the centre",
   "desc": "a slim leather writing-slope open on the box rail, a portable terminal resting on it",
   "puzzle": true,
   "label": "The writing-slope terminal"
  },
  {
   "id": "lighter",
   "at": "just right of centre",
   "desc": "a monogrammed silver flip-top lighter lying close to the viewer and large in the frame on the velvet seat, tilted so the light off the stage rakes bright across its upturned face, a single bold deeply-cut house crest filling that whole face, the crest a simple engraved heraldic device with no words, initials or lettering of any kind",
   "clue": true,
   "label": "A monogrammed lighter"
  },
  {
   "id": "back",
   "at": "to the right",
   "desc": "a curtained doorway back to the corridor",
   "door": {
    "direction": "open",
    "to": "briefing"
   },
   "label": "The way back"
  },
  {
   "id": "on",
   "at": "on the far right",
   "desc": "a second curtained doorway giving onto the grand stair",
   "door": {
    "direction": "open",
    "to": "a_townhouse"
   },
   "label": "On to the next call"
  }
 ],
 "atmosphere": "evening, hot gilt and crimson, the stage a small brilliant source far below, deep warm shadow in the box, painterly, cinematic, film grain",
 "negatives": "No people, no figures, no crowds, no lettering, no captions, no text, no signage, no numbers.",
 "continuity": []
}
```
WHY: The single change is the `lighter` element's desc — flip-top rather than a flat case, close to the viewer and large in frame, tilted into the stage light, one bold deeply-cut wordless crest filling its face — fixing the illegible smeared marque on a ~110 px shadowed slab, and it is worth spending attempt 3 on because verification against `scene_specs_heist.json` shows this wording was never actually applied on attempt 1, so the diagnosed fix has not yet been tested even once.