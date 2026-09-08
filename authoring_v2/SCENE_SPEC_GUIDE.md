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
  "seamOccluder": "a riveted iron stanchion, floor to ceiling",  // the object the SECOND-PASS occluder repair stands on the seam (rule 5a). Not rendered into the prompt.
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

### ⚠️ RULE ZERO — STATE THE RELATIONSHIPS, NOT JUST THE OBJECTS

**Read this before writing a single element.** It is the most expensive lesson in the corpus: it cost
`networks/subway` roughly a dozen art rounds across two days, and every single one of those failures
was the same mistake wearing a different coat.

**A spec is a list of elements, and the model renders each one faithfully and INDEPENDENTLY.** It will
give you a beautiful train and a beautiful platform and a beautiful tunnel mouth, and it has no reason
whatever to put the train on the rails, or the rails into the mouth, unless you said so. Describing
each object well is not enough. **What has to be stated is how they JOIN.**

The four that cost subway its rounds, all found by eye on generated art, none catchable by
`validate_scenes.py` (they are semantic, not structural):

| the two things | what came back |
|---|---|
| the train and the platform's section | trains standing *beside* the rails on a flat floor, or on ballast laid on the platform |
| the roads and the station's ends | one lone arch dead ahead on the *platform's* axis, with no rails running into it |
| the buffer stops and the direction of travel | a barrier between a train and the very mouth its line has to leave by |
| the rails under the train and the rails leaving the station | two separate railways in one picture, the train on a stub that reaches nothing |

**The diagnostic, and it is quick.** Go through the elements in pairs and ask of each pair that must
physically relate: *if these two were drawn independently, would anything be wrong?* If the answer is
yes — and for anything load-bearing it usually is — the join is not optional and must be written.

**Three things about HOW to write a join, each learned the hard way:**

1. **Put it in BOTH elements, and again as a refusal in `negatives`.** A relationship stated in one
   element only does not reliably hold; the other element is what the model is looking at when it gets
   it wrong. Subway's rail alignment had to be in the road element *and* the negatives before it took.

2. **A fact about the SHAPE of a room must be an ELEMENT, not a negative.** Negatives suppress things
   the model wants to draw; they do not build geometry. Subway's track-bed clause sat in `negatives`
   for two days and rendered *not once*; the same fact promoted to a foreground `platform_edge`
   element — written in depth order, nearest first — worked immediately.

3. **Write it in depth order, nearest first**, for the same reason as rule 0c: clause order decides
   what a subject attaches to. *"the edge at your feet, then the drop, then the bed, then the rails in
   it, then the train standing on them"* renders; the same facts in any other order do not.

**And say counts as numerals** (rule 0e) — a relationship often implies a count, and "each road has its
own bore" becomes reliable only when it is also "there are EXACTLY 4 tunnel mouths in this station".

0. **Never name the structure you are STANDING ON as if it were in view** (2026-08-07, the Pharos gallery).
   `setting` reads as *"a panorama from …"*, but gpt-image treats a named landmark as **something to draw**,
   not a vantage to adopt — so `"from the gallery at the top of the Pharos lighthouse"` reliably paints a
   second lighthouse into the scene. It compounds when neighbouring rooms legitimately show that landmark,
   because the model's prior for the whole world then includes it. Two fixes, apply both: state the vantage
   **positively** ("the viewer is standing ON the tower's own topmost platform, surrounded by its parapet and
   columns"), naming the structure by *function* (sea-tower, lamp chamber) rather than repeating the landmark
   noun; and put an explicit exclusion in `negatives` ("no tower or beacon anywhere in the view — the viewer
   is standing on top of the only one"). Reinforce it locally in whichever element keeps growing the thing
   (here the harbour sweep: "the harbour is low and flat, no tower standing anywhere in it"). Generalises to
   any *interior-of-a-landmark* scene — inside the airship, atop the henge, within the vault.
0a. **Every claim about the SAME REGION must agree** (2026-08-07, the Pharos summit). Two elements each
   described what lay below the tower — one said moored ships lay "directly below on the near stone quay",
   the other wanted an island in open water — and the model resolved the contradiction by painting the
   tower attached to the wharf, the opposite of the design. It does not arbitrate between conflicting
   statements about one part of the frame; it blends them. Before generating, read the `elements` as a set
   and check the ground, water, sky and horizon are each described **once, consistently**. A leftover
   phrase from an earlier fix is the usual source.
0b. **State what is NOT there, in `negatives`.** A positive description alone will not suppress something
   the model's prior wants to draw. The tower reads as island-bound only once `negatives` explicitly bars
   "a causeway, bridge, mole, jetty or any buildings at its foot", and the phantom second lighthouse goes
   away only once "no tower or beacon anywhere in the view" is stated. Whenever you are relying on the
   *absence* of something — a connection, a second copy of a landmark, people, lettering — name that
   absence rather than hoping the positive description implies it.
0c. **Clause ORDER decides what a subject attaches to.** gpt-image binds a subject to whatever was named
   just before it, so "open water, with the ship at the quay" tends to put the ship in the open water,
   while "the stone quay, with the ship moored alongside it" holds her at the quay. **Name the anchor
   first, then the subject, then the open space** — never the other way round. This is the same failure
   as 0a from the other side: 0a is two elements disagreeing about one region, 0c is one sentence
   attaching a subject to the wrong half of itself.
0c-bis. **The equirectangular clause is EMITTED FOR YOU — do not write your own** (2026-09-07).
   `render_prompt` now appends a standard `EQUIRECT` sentence to every scene prompt in every scenario:
   the walls wrap continuously with strong barrel curvature, ceiling and floor bow across the frame,
   surfaces near the frame edges are at the viewer's *side* seen at a glancing angle, and it is never a
   flat frontal elevation, a single-vanishing-point composition, or a view of the room from outside it.
   It came out of `networks/subway`, which produced the best equirect images in the corpus, and it lives
   in the renderer rather than in each scenario's `negatives` **so that no author has to remember it and
   no scenario can be missing it**. Interiors need it most — a small box of a room is where the model
   most wants to give you one wall seen head-on.

0d. **KEEP `setting` TO ONE SENTENCE — a long one flattens the projection** (2026-09-06,
   `networks/subway` `car_woad`). `render_prompt` opens with *"This is a seamless 360-degree panorama
   from {setting}"*, so everything in that field is read as a description of the VANTAGE. Grow it into
   a paragraph — narrating which end of the room lies left, which lies right, what is behind the
   viewer, plus a block of surface condition — and the model stops rendering a place and starts
   rendering a **composition**: a flat, rectilinear elevation of one wall, parallel walls, no barrel
   curvature, a corner returning at each frame edge. Three candidates were lost to this before the
   cause was found. **The evidence:** `beacons/whistlegate`, the only interior in the corpus that has
   ever wrapped correctly, has a **one-sentence** setting.
   - **The geometry belongs in the elements' `at` positions, not in `setting`.** Stating it in both
     places is what breaks it — the positions already place things left, right and behind.
   - **Condition, materials, palette and clutter belong in `atmosphere`**, which is the field for them.
   - Reinforce with a negative, because a positive description will not suppress the flat reading:
     *"This is an EQUIRECTANGULAR 360 panorama, not a flat photograph: the walls wrap continuously
     right around the viewer with strong barrel curvature, the ceiling and floor bow across the frame,
     and any surface toward the left or right of the frame is at the viewer's SIDE, seen at a glancing
     angle rather than face-on. NOT a flat frontal elevation of one wall, no single-vanishing-point
     composition, and never a view of the room from outside it."*
   Interiors are the dangerous case: a small box of a room is where the model most wants to give you
   one wall seen head-on.

0e. **STATE A COUNT AS A NUMBER, or you will not get that many** (2026-09-06, `networks/subway`
   `alum_wharf`; second instance — the first was `beacons` `crown/scene_order_sent`, which drew THREE
   distant fires for a scenario whose escape turns on there being FOUR). Anything the player must be
   able to count, or that the puzzle logic depends on, has to appear in the prompt as a numeral **and**
   be fenced with a negative barring extras. Alum Wharf berths two lines and its four berth
   elements — two doors on each of two trains — rendered as **three separate trains**, because each
   element reads as its own object unless the frame is told how many objects there are. The fix that
   worked: *"There are EXACTLY 2 trains in this station, one at each platform face and NO OTHERS — do
   not add further trains, carriages or wagons anywhere in the frame or receding down any tunnel."*
   Note that `beacons`' own notes had already concluded *"treat any exact count in a generated frame
   as unreliable"*; this is the constructive half of that rule.

0f. **A still bound for a cinemagraph must be explicitly SHARP.** Describing something as *sliding
   past* or *running* invites the model to paint the motion INTO the still as motion blur and smeared
   detail, which is the wrong input for the cinemagraph stage: the still should be crisp and the
   movement should come from the clip. Cost the woad cab one candidate. Add to `negatives`: *"The image
   is SHARP: no motion blur, no streaking, no smeared or doubled detail anywhere — everything in this
   picture is standing still, and any movement described is what the cinemagraph will add later, never
   something painted into the still."*

1. **Left-to-right sweep.** Order `elements` as they appear sweeping around the panorama. Each `at` is a
   spatial phrase. **There are exactly SEVEN positions and seven phrases — one name each:**
   `on the far left (0.08) · to the left (0.20) · just left of centre (0.36) · dead ahead in the centre
   (0.50) · just right of centre (0.64) · to the right (0.80) · on the far right (0.92)`. These drive BOTH the
   prose order AND the approximate hotspot x-position, so spread them across the whole ring.
   **Seven is the real ceiling, so plan the ring around what actually needs a BOX.** The default approx
   box is 0.16 wide while adjacent positions sit 0.12–0.16 apart, so neighbouring boxes already abut —
   an eighth position would not separate anything. This list used to name eight phrases for these seven
   places ("to the centre-right" was a second name for 0.64, and there was no name for 0.36's left-hand
   twin), which reads as an extra slot that does not exist and lands two elements on one x. Only elements
   that need a box — a gameplay hotspot, or an `animate` motion subject — genuinely conflict; backdrop
   and scenery may share a position freely, and `validate_scenes` only warns when both sides need a box.
   A room wanting more than seven distinct places is usually one where a global architectural fact (side
   arches, a gallery running right round) belongs in `setting` rather than in an element of its own.
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
3. **Animatable objects — declare them up front, framed to move.** Flag `animate:{motion, loop}`.
   **⚠️ `animate` NO LONGER CREATES A HOTSPOT (2026-09-02).** Motion is now baked over the WHOLE panorama,
   per (room, world-state), by `cinemagraph_tools/cine_scenario.py` from an authored `authoring.motionSpec`
   — not as a per-object box clip. So `animate` is now purely the SOURCE TEXT for that motion spec: keep
   declaring what moves and how, but expect no `ambient` carrier and no queued job per object. The two
   carriers that DO still exist are the full-scene variant carrier (box `[0,0,1,1]`, created by the
   harness) and an `animate` element that also declares `variants` — that one keeps its carrier because a
   BOXED state variant needs somewhere to hang.
   Everything below about framing an object to move still applies: it is what the motion spec is written
   from, and a thing framed so it cannot move still will not move. Frame the
   object so it CAN move: "a lantern **on a chain**" (not fixed to a post), "steam **venting**", "a flag",
   "bubbling liquid", "drifting embers". Name ONE physical motion + a pace. Prefer **movement over
   brightness** — "twinkling lights" barely moves; give it a carrier ("steam drifting past the indicator
   lights"). Good animatables: flame/fire, steam/smoke, water/liquid surface, bubbling vessels, hanging
   lantern/chains swaying, sail/flag, gauge needles, drifting cloud, embers, dust motes, turning dial/gears.
3a. **ANGULAR SIZE decides whether a subject can animate — not what kind of thing it is** (2026-09-02,
   measured across `networks/beacons`' 25 cinemagraph states). The "good animatables" list above is
   necessary and *not* sufficient: the same subject lives or dies on how big it is in frame.
   The measurements, all from one scenario and one pipeline:
   - Village lamps scored **20.6 at Fenwatch and 22.1 at the Ladder (alive)** where they are near and large,
     and **2.0–3.6 (DEAD)** at the Spindle, Ram's Head, Hood, Shears, Kiln and the Crown's payoff frame,
     where they are distant points. Repair did not rescue a single one.
   - Smoke: the Anvil's **fat near column, 14.4 alive**; Fenwatch's **thin far column, 2.4 dead**, still
     dead after repair.
   - What worked everywhere was big and soft: spindrift off a rock face (9–21), a braided river's channels
     glinting (10–17), a hearth (8.5), a summit brazier (22.8).
   **The rule:** a motion subject must occupy a substantial, contiguous, soft-edged region of the frame and
   move as a continuous body. **Point-like, high-frequency, far-away detail cannot be animated by this
   pipeline** — grass, foliage texture, animals, distant windows and lamps, thin distant smoke, crowds.
   Declaring them costs a generation and a repair cycle and returns DEAD.
   **If a scene's only life is far away, that is a FRAMING problem, not a motion-spec problem.** Fix it by
   moving a large carrier into the near or middle field — the room's own fire lit, a lantern on the parapet,
   cloud crossing in front of the viewer, water close enough to read — rather than by asking harder for the
   distant thing to twinkle.
3b. **Give each room a DIFFERENT hero motion.** One dominant, room-specific movement, chosen so no two
   neighbours share it. Beacons authored the same two subjects — spindrift off a crag, river glint below —
   into all eight ridge rooms; every one of them measured alive, and the scenario still read as static,
   because identical motion everywhere is indistinguishable from a still world with a screensaver on it.
   Motion is a differentiation channel; spend it (see *Cross-room differentiation*).
   **A clear sky is a motion budget spent on nothing.** If the world's palette rules out overcast, the sky
   can still carry the room: banner cloud streaming off a summit, stacked lenticulars, a cloud inversion
   filling the valley *below* the viewer with peaks standing out of it. All are hard-sun, deep-blue-sky
   phenomena, all are enormous and soft-edged, and all satisfy 3a.

4. **Loop mode.** `boomerang` = oscillating (flame, water, flag, sway, needles). `crossfade` = directional /
   rising / one-way (steam, smoke, rising bubbles, embers, drifting cloud, a turning dial or gears).
5a. **DEFAULT SEAM RECIPE — generate normally, then PLANT AN OCCLUDER as a second pass (2026-08-26, Lucas).**
   The first-pass prompt does the ordinary thing (rule 5: a calm `seam` backdrop). Then, in the wrap menu of
   the per-room hub, run **④ Plant an occluder**: the tool rolls the seam to the centre of the frame,
   crop-inpaints only a band around it, and stands an object there running the full height — explicitly
   "so the two sides do not need to match each other" — keeping the outer thirds pixel-identical and
   feathering the band back in. **That last part is why it works:** the model only paints a local band with
   real original art as context on both sides, and the composite blurs the two boundaries between the
   planted object and the untouched wrap. Lucas: reliable enough to be the default, and the step that
   most nearly automates art generation away.
   **Author it up front — set `seamOccluder`** on the spec (e.g. `"a plain sandstone pillar, floor to
   ceiling"`): a short in-world description of what should stand on the seam. It is NOT rendered into the
   first-pass prompt — it is the second pass's input, kept with the rest of the room's authoring so the
   repair needs no fresh decision at art time.
   **Choose an object with no continuous structure to line up:** a pillar, a column, a rock spire, a
   hanging curtain, a tree trunk, a heavy timber post. Full height, vertical, static.
   **The one thing that does NOT work is asking for a straddling object in the FIRST pass** — there the
   model must draw one half at each extreme edge and make them agree, which is harder than a flat backdrop.
   Occluding is a second-pass operation on an existing panorama, never a first-pass instruction.

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
2. Per room — generate art from the rendered prompt → judge it → commit. Art is the expensive step, so
   this is where the money goes. Two ways to run it, both owned by the `escape_room_stills` skill:
   **by hand** (generate, review the candidates with `art_qc.py` at NATIVE resolution, commit), or
   **unattended** via the `stills_iterate` long_agent loop, which does the same thing overnight for a
   whole scenario and leaves an accept queue. Neither ever marks art accepted — that stays human.
   (Continuity: use the world plate / room-reference for rooms that must match a seen landmark.)
2a. **SEAM STAGE — `seam_stage.py` (screen → blur → occlude → accept).** Required, and required HERE:
   variants, cinemagraphs and door-opens are all baked FROM `scene.png`, so a seam repaired afterwards
   does not repair them. Blur before occluder, never after. Nothing is done until a human accepts; the
   verdict is recorded on the room and `run_all_tests.py` gates on it. See `authoring_v2/AGENTS.md`.
2b. **DRAFT THE BOXES — `place_hotspots.py` (gpt-4o localizer).** Grid-on-image + the generation prompt
   for left-to-right ordering; refuses to write a run whose predictions collapse. Produces
   `boxSource: draft:localizer`, which step 4 then corrects.
3. `POST /api/apply-spec-all {chapter, scenario}` — materialises approximate hotspots + queues every animated
   element's cinemagraph **and every door open-view** (as a state-tagged door-open variant) across the scenario.
4. Per room (HUMAN box-review — the deliberate human step): nudge/resize the rough boxes in the hub flat
   editor; draw wrap boxes for any seam object.
5. Bake the motion: `cinemagraph_tools/cine_scenario.py` walks every (room, world-state) and renders the
   WHOLE panorama from that state's `motionSpec` — including the night variants, which carry their own
   motion. (The old per-hotspot 5-candidate box batch is retired; `wrangling/egypt` was the first scenario
   with zero box clips, and `networks/beacons` was authored this way from the start.)

## Worked example
`authoring_v2/scene_specs/airship_boss.json` — the airship engine room, built from its real prompt + ambient
objects. `python3 scene_spec.py scene_specs/airship_boss.json` shows the full round-trip (prompt + the 7
cinemagraphs + the hotspot stubs that fall out).

## The world plate is the highest-leverage prompt in the scenario (2026-08-27)

Every room is generated with the world plate as its `--ref`, so **whatever the plate assumes, all nine
rooms inherit** — including things nobody decided. temple's plate opened *"a **ruined** jungle temple"* and
specified *"PALETTE: **near-monochrome** — **desaturated** … every other surface is **muted**"*, and both
propagated into every room and into the shared `atmosphere` tail. The result contradicted the scenario's own
premise (a keeper who died **last month**, a temple closed forever *unless* the registers exist — stakes
that need a living building) and it measured as the least saturated scenario in the corpus by a wide margin:
mean saturation 0.22, against trees 0.39, egypt 0.48, airship 0.71.

**So the plate must state CONDITION, not just light and palette.** Kept / working / recently abandoned /
long ruined is a decision with as much reach as the time of day, and if you don't make it the model picks
one from the setting's idiom — "jungle temple" ships with ruin attached.

**Desaturating the world is not how you make a keyed colour readable.** temple went near-monochrome so nine
banner colours would stay tellable apart. Re-authored to *"the banners are the only PURE, fully saturated
colour — nothing else competes with them for chroma — but the world around them is rich and alive"*, mean
saturation went 0.21 → 0.56 **and the banners went up too**, peaking at 0.98 vs 0.68. Reserving the top of
the chroma range works; draining everything else just makes a grey scenario.

**A room whose condition is the exception needs its own clause.** A blanket "the temple is kept, nothing
ruined, no rubble" clause contradicts a room that is *supposed* to be four centuries untouched, and a
contradictory prompt gets you neither. temple's sealed cell and service crawl carry their own condition
sentence and inherit only the palette.

## Cross-room differentiation — author the specs as a SET (2026-09-02, beacons)

The world-plate section above is about what every room should **share**. This is its counterweight, and it
is the failure the plate makes easy: **inheritance is for palette, light, condition and materials — never
for landform, outlook, foreground or motion.**

**What went wrong in `networks/beacons`.** Eight of the nine ridge posts were authored from one template.
Identical `setting` sentence, word for word. Identical `seam`, identical `seamOccluder`, identical approach
path ("arriving along the bare ridge crest from the south"), identical spyglass, identical cold fire
basket. The one large element — the view down into the valley — was the same sentence in all of them,
differing only in a **count of distant villages**: three, four, nine, a dozen. At render scale that is
invisible. The player walks eight rooms that look like one room and cannot tell where they are.

**The cover test.** Cover the small named object that gives each room its name. If two rooms are now
indistinguishable, they are the same room, and the name is doing work the art should be doing.

**Differentiate on the BIG things**, in roughly this order of visual weight: the landform the viewer stands
on · what the ground does at their feet · what fills the middle distance · where the light comes from and
which way the shadows fall · the hero motion (3b). A named crag off to one side is a label, not a place.

**Never differentiate rooms by a countable quantity of small distant objects.** It fails twice over: it is
unreadable at render scale, and where it *is* readable it leaks whatever data the count encodes.

**For a "survey of places" scenario — where the rooms genuinely ARE different locations — decide the whole
set of landforms FIRST, before any spec is written**, and check for repeats across the set. Writing specs
one room at a time makes the template the path of least resistance every single time.

**Check the approach direction against the map.** If the scenario has real coordinates, the path into each
room should arrive from the bearing the player actually travelled. Beacons said "from the south" in every
room; only three of its nine legs were southerly, and the legs ranged from under 4 km to 15 km with one
1,490 m ascent. Approach direction and leg character are free differentiation that the topology has
already decided for you. (`escape_room_scene_validator` checks passage *pairing*; bearing is on the
spec-author.)

**Art fidelity is not a puzzle-leak vector, and treating it as one is expensive** (Lucas, 2026-09-02).
Beacons deliberately flattened its views so no player could read the coverage answer off a painting. That
threat was never real — it needs a level of attention and of rendered fidelity that does not exist — and
defending against it consumed the scenario's entire differentiation budget. **Puzzle data is protected by
where it is wired, not by making the art vague.**
