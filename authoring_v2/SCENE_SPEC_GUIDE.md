---
authority: reference
---

# Scene spec authoring guide (the "spec-author")

The **scene spec** is the single structured input the automated art pipeline derives everything from — the
gpt-image prompt, the cinemagraph batch jobs, and the hotspot stubs all fall out of it (see
`scene_spec.py`; design + phasing in `notes/art_pipeline.md`). The spec-author is **Claude**: given a room
network and a description of vibes, Claude drafts **one spec per room** following the rules below.

## Inputs → output
- **Inputs:** the room network (which rooms, how they connect via doors), a description of the world/vibes,
  and each room's role/story beat. (For a full CHEM 5725 scenario these come from `escape_room_puzzles` +
  `escape_room_story`.)
- **Output:** a JSON object `{"worldPlate": "<prompt>", roomKey: spec, ...}` for the whole scenario, ready for
  `POST /api/save-scene-specs`. **`worldPlate`** (optional, scenario-level) is a "world-bible" establishing-image
  prompt — pack the key elements + palette into one frame, written **TIME-NEUTRAL** (soft even daylight, neither
  dawn nor sunset) so each room's own prompt still drives the time-of-day arc. It's generated FIRST in build-world
  step 2 and referenced by every room's gen for cross-room continuity, and it lives in this same bundle (single
  source of truth) — not a separate field. (Caveat: gpt-image-2 references it at high fidelity, no loosen knob —
  it can flatten the light arc at the extremes; a deep-dark or bright room may want to skip the reference.)

## Schema (per room)
```json
{
  "room": "<roomKey>",
  "setting": "the centre of the engine room at the heart of a steampunk airship",
  "interior": true,
  "seam": "a plain, continuous stretch of riveted brass bulkhead, uniform and unbroken",  // ALWAYS SET: the calm, low-detail backdrop directly BEHIND the viewer, split across the extreme L/R edges (see rule 5)
  "elements": [           // ORDERED left → right as they sweep around the 360
    { "id": "boiler", "at": "on the far left", "desc": "a riveted boiler, its firebox door ajar",
      "animate": { "motion": "the firebox glowing and flickering", "loop": "boomerang" } }
    // one role per element: animate | puzzle:true | switch:true | door:{direction,to[,opensOnto]} | clue:true | lock:true | grid:true | dial:true
    // label           = the IN-WORLD name ("The customs writing-desk"). Set it on anything the player opens:
    //                   it is the play-time MODAL TITLE, and the key pre-art `plannedHotspots` content
    //                   slug-matches on when it attaches at commit. Omitted ⇒ falls back to desc[:60].
    // switch:true      = a world-state CONTROL (lever/dial/valve): placed + boxed like a puzzle but NOT graded; wiring sets its state effect.
    // door.opensOnto   = [{state,reveal},…] a door with >1 open-view (a monorail car whose switch picks which station it looks out on):
    //                    each view -> a state-tagged door-open variant on the ONE door hotspot; runtime pick-by-state is deferred wiring.
  ],
  "atmosphere": "hot amber-and-red furnace glow, brass highlights, heavy haze and steam, film grain, tense",
  "negatives": "No people, no lettering, no captions, no text",
  "continuity": []        // reserved (phase 2): [{ "element": "<id>", "landmark": "<name>" }]
}
```

## Rules
1. **Left-to-right sweep.** Order `elements` as they appear sweeping around the panorama. Each `at` is a
   spatial phrase — `on the far left · to the left · to the left of centre · dead ahead in the centre ·
   just right of centre · to the centre-right · to the right · on the far right`. These drive BOTH the
   prose order AND the approximate hotspot x-position, so spread them across the whole ring.
2. **Every room needs its door(s).** Add a `door` element per the network — `door:{direction:"forward"|
   "back"|"open", to:"<roomKey>"}`. The forward door gates on the room's puzzle; a gateless "reading" room
   uses a `back` door (engine mechanic — see `AGENTS.md`). **Multi-view door:** a single door that looks out
   on more than one place (a monorail car whose world-state switch picks which station it opens onto) carries
   `opensOnto:[{state,reveal},…]` — one reveal prompt per destination. All the open-door art is generated in
   the art step (each becomes a state-tagged door-open variant on the ONE door hotspot); runtime pick-by-state
   is deferred wiring. It stays ONE door box — preferable to a wall of separate in/out doors.
   **A door that boards a vehicle IS the vehicle's own door.** Describe "a gondola docked at the platform,
   boarded through its own sliding door" — NOT "a boarding door, with a car waiting beyond it": the latter
   makes the model render the door and the vehicle as two separate objects (trees stations, 2026-08). One
   object: the vehicle, boarded through its own door.
3. **Animatable objects — declare them up front, framed to move.** Flag `animate:{motion, loop}`. Frame the
   object so it CAN move: "a lantern **on a chain**" (not fixed to a post), "steam **venting**", "a flag",
   "bubbling liquid", "drifting embers". Name ONE physical motion + a pace. Prefer **movement over
   brightness** — "twinkling lights" barely moves; give it a carrier ("steam drifting past the indicator
   lights"). Good animatables: flame/fire, steam/smoke, water/liquid surface, bubbling vessels, hanging
   lantern/chains swaying, sail/flag, gauge needles, drifting cloud, embers, dust motes, turning dial/gears.
4. **Loop mode.** `boomerang` = oscillating (flame, water, flag, sway, needles). `crossfade` = directional /
   rising / one-way (steam, smoke, rising bubbles, embers, drifting cloud, a turning dial or gears).
5. **Seam awareness — set the `seam` field, keep it on continuous backdrop.** The far-left and far-right edges
   are the SAME line (the ±180° wrap seam, directly behind the viewer), so they must join cleanly. **ALWAYS set
   the `seam` field** to that backdrop — a calm, low-detail, continuous surface (open sky / canopy / a plain
   wall); `render_prompt` injects it at the HEAD and TAIL of the prompt, telling gpt-image the two edges are the
   two halves of that one surface so they line up instead of clashing. It's the single biggest lever on seam
   quality (added 2026-08 after seams proved hard under the fully-described 360 spec). **Keep that seam surface
   boring — and put the structural objects (doors, instruments, vehicles) in the FRONT hemisphere, away from the
   edges.** The reliable pattern for an
   exterior: two matching backdrop elements, one `on the far left` and one `on the far right`, each described
   as the open view "that meets cleanly at the seam directly behind you" — then the wrap is backdrop-to-
   backdrop and joins trivially. **Do NOT run a linear feature off an edge** (cables, tracks, beams, long
   rails) — gpt-image won't continue a thin line across the seam, so frame attached lines (a car's cables) to
   run UP / vertically or terminate, not stretch toward the edge (learned on the trees stations, 2026-08).
   Animatable objects especially stay off the extreme edges (a seam-crossing cinemagraph needs a hand-drawn
   wrap box — avoid it by placement). If an object genuinely must straddle the seam, the human draws a wrap
   box in the flat editor (the engine rolls + splits).
6. **Gameplay elements** — `puzzle:true` (the graded object; grading is wired separately in the harness),
   `switch:true` (a world-state control — lever/dial/valve; placed + boxed now, its state effect wired later —
   kept distinct from `puzzle` so real graded puzzles aren't confused with switches), `clue:true`, and the two
   ungraded escape gates — **`lock:true`** (keypad flavour) or **`grid:true`** (the matrix-select flavour,
   mechanic #15). Pick the one the escape actually uses: the engine dispatches on the hotspot `type`, so a
   grid-select escape emitted as a `lock` silently fails to open. One role flag per element.
   Also set **`label`** on every gameplay element — see the schema note above.
   **`dial:true`** emits type `dial`, the engine's own world-state control (`openDial`). Prefer it over
   `switch:true` whenever the control IS a dial/lever the player turns: the engine has **no `switch`
   handler**, so a `switch` hotspot is inert until someone hand-reclassifies it (every trees drive-lever had
   to be).
8. **State-variants — `variants:[{state, when?, reveal}]` on ANY element.** The general case of a door's
   `opensOnto`: an alternate look that shows when `when` holds (`pickActiveVariants`). Each one with a
   `reveal` is queued as a variant job by *Place all hotspots* and rendered in the normal art batch, so
   payoff art (the Pharos lamp swinging its beam onto the player's ship) can't be forgotten. Put it on an
   `animate` element when it should carry art but no player marker — an `ambient` hotspot is exactly that.
7. **Atmosphere** — a vivid closing line: light, mood, materials, haze/grain. **Negatives** — default
   "No people, no lettering, no captions, no text".

## Pipeline after authoring
1. `POST /api/save-scene-specs {chapter, scenario, specs:{roomKey:spec}}` — stores every spec + renders every
   prompt into `authoring.scenePrompt`.
2. Per room (HUMAN, art is the expensive step): Generate art from the rendered prompt → pick a candidate →
   commit. (Continuity: use the world plate / room-reference for rooms that must match a seen landmark.)
3. `POST /api/apply-spec-all {chapter, scenario}` — materialises approximate hotspots + queues every animated
   element's cinemagraph **and every door open-view** (as a state-tagged door-open variant) across the scenario.
4. Per room (HUMAN box-review — the deliberate human step): nudge/resize the rough boxes in the hub flat
   editor; draw wrap boxes for any seam object.
5. Run the batch → each cinemagraph renders **5 candidates**; pick the liveliest per hotspot.

## Worked example
`authoring_v2/scene_specs/airship_boss.json` — the airship engine room, built from its real prompt + ambient
objects. `python3 scene_spec.py scene_specs/airship_boss.json` shows the full round-trip (prompt + the 7
cinemagraphs + the hotspot stubs that fall out).
