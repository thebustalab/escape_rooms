FINDINGS: I opened all six native strips (strip1–strip6) plus close crops of the matchbook (/tmp/matches.png), the trolley terminal (/tmp/trolley.png), and a left/right wrap composite of the seam (/tmp/seam.png). Checklist object by object: the **evidence locker** is present in strip 1, a steel panel set flush into the marble wall with a dark keypad, well-formed and easily boxable; the **conservator's terminal** is present at the strip 3/4 join, an open portable terminal on a wheeled trolley, correctly scaled and clearly readable as a machine; the **book of matches** is present in strip 4 on the floor beside a plinth base at roughly x≈1990, small but a legible flat matchbook, not a smudge; **the way back** is the arch in strip 4 with stair-hall steps visible beyond it, on the right bearing; **on to the next call** is the propped fire door in strip 5 giving onto a lit service corridor, again on the right bearing and unmistakably a different passage from the arch. The **hotel key fob (TOKEN 3/5) is nowhere in the image** — and the reason is upstream, not in the render: the sceneSpec's `elements` list has seven entries and none of them is the fob, so the prompt never asked for it. That is the Beacons anvil failure exactly: a `clue` hotspot with nothing to attach a box to, and this one is a token in a five-token chain, so the room ships broken. Everything else is strong — the seam is genuinely excellent (plain dark veined marble on both edges, baseboard and floor banding running straight through the join, no object crossing, no tone step), the glazed barrel roof and moonlight are as commissioned, the dust sheet and emptied vitrine with its felt-bed impression are both there, one warm low security lamp is in strip 5, and I found no generated lettering anywhere. It is a shame to burn a good render, but the fix is a spec fix and cannot be repaired downstream.

DECISION: REGENERATE
SPEC:
```json
{
 "room": "a_gallery",
 "setting": "the centre of a marble sculpture hall in a great museum after closing, a glazed barrel roof overhead and empty plinths receding on both sides",
 "interior": true,
 "seam": "a plain stretch of cold veined marble walling, uniform and unbroken",
 "seamOccluder": "a square marble pier running floor to ceiling",
 "elements": [
  {
   "id": "locker",
   "at": "to the left",
   "desc": "a steel evidence locker set into the wall, its keypad dark",
   "lock": true,
   "label": "The evidence locker"
  },
  {
   "id": "fob",
   "at": "to the left",
   "desc": "a sealed clear plastic evidence bag holding a single small hotel key fob, its label blank, resting on a low marble ledge directly beneath the evidence locker",
   "clue": true,
   "label": "A hotel key fob"
  },
  {
   "id": "sheet",
   "at": "just left of centre",
   "desc": "a canvas dust sheet draped over a near plinth, lifting and settling in the draught from a propped fire door",
   "animate": {
    "motion": "the canvas dust sheet lifting and settling slowly over the plinth",
    "loop": "boomerang"
   }
  },
  {
   "id": "vitrine",
   "at": "just left of centre",
   "desc": "a tall glass vitrine standing open and emptied, its felt bed still showing the impression of what stood there"
  },
  {
   "id": "console",
   "at": "dead ahead in the centre",
   "desc": "a portable terminal open on a conservator's trolley",
   "puzzle": true,
   "label": "The conservator's terminal"
  },
  {
   "id": "matches",
   "at": "just right of centre",
   "desc": "a book of matches dropped by the plinth, an address printed inside the cover and half burnt away",
   "clue": true,
   "label": "A book of matches"
  },
  {
   "id": "back",
   "at": "to the right",
   "desc": "an archway back toward the stair hall",
   "door": {
    "direction": "open",
    "to": "a_townhouse"
   },
   "label": "The way back"
  },
  {
   "id": "on",
   "at": "on the far right",
   "desc": "a propped fire door giving onto a service corridor",
   "door": {
    "direction": "open",
    "to": "a_vault"
   },
   "label": "On to the next call"
  }
 ],
 "atmosphere": "the small hours, cold moonlight falling through the glazed roof onto white marble, one warm security lamp low down, long hard shadows, painterly, cinematic, film grain",
 "negatives": "No people, no figures, no crowds, no lettering, no captions, no text, no signage, no numbers.",
 "continuity": []
}
```
WHY: The single change is adding the missing `fob` element — an evidence-bagged hotel key fob on a ledge beneath the locker — so that TOKEN 3/5's clue hotspot has an object to box, which the current spec (and therefore the render) does not provide.