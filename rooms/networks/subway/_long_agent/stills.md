# Stills iteration — networks/subway

11 room(s) in scope after 78 cycle(s).

## hold (2)

### cropping_yard — 3 attempt(s)
`l1_cropping_yard_1.png`
- It is the only candidate, and it clears everything that is expensive to fix later — all five checklist objects depicted and well-formed, four genuine open cab doorways on two double-ended units, both through tunnel mouths, no lettering, and a seam that wraps cleanly with rivet courses aligned — leaving only a level-relationship shortfall that two targeted spec rewrites have already failed to move and that breaks nothing downstream.

**Concerns — the loop committed this but was not sure:**

Two things for Lucas's eye. (1) The platform/track-bed level is still short of spec — a shallow trough rather than a waist-deep bed, and no raised platform with a square granite edge, so boarding reads as a knee-high step up into each cab rather than a step across. This is the defect attempts 1 and 2 each tried to fix by rewriting `setting`; it is materially better here than attempt 1 (there is a sunken road now, and the units are broadside-on with all four cabs in view) but it is not what the negatives ask for, and I can't tell from the images whether a third `setting` rewrite would move it or whether the model simply won't render a raised platform underfoot in an equirectangular 360. (2) Shared-world colour: this frame is close to a uniform warm amber wash, against a world plate that demands cold blue-green occupying at least as much of the frame as the warm amber and explicitly forbids a uniform brown cast — worth comparing side by side with the other committed subway rooms, because if they all came out this warm it is a scenario-wide look rather than this room's problem. Related: the wall lichen that the world plate calls the most important thing in frame is absent here (the orange is paint and rust, and the crop appears only as cut crust in the bench trays) — but this room's own spec never asked for it on the walls, so that gap is upstream in the spec, not in the render. Nothing I found blocks wiring: all five hotspots have a well-formed object to box.

### tannery_row — 3 attempt(s)
`l1_tannery_row_1.png`
- It is the only candidate, all five checklist objects are depicted and well-formed, the seam joins cleanly on plain tile with nothing crossing it, and on attempt 3 of 3 the remaining faults are ones you can judge by eye while a rejection would leave the room dead and every downstream stage blocked.

**Concerns — the loop committed this but was not sure:**

Three things for your eye. (1) Extra rolling stock: at least four additional dark wagons stand at the far end of the platform on both roads (~x1455–1530 and ~x1560–1620) receding toward the centre tunnel mouth, against the "exactly 2 trains, no vehicle receding into a tunnel" rule — they are small, unlit and carry no doors, so they read as background works stock, but they are a real spec violation and if you want them gone it is a re-roll, not a repair. (2) The two named units do not visibly sit on rails: their solebars meet the walkway paving and their underframes drop into unlit shadow with no wheels, sleepers or running rail beneath them, even though proper ballast beds with rails are correctly rendered behind the viewer, at both platform ends and beyond the green unit's far side. This was attempt 2's target change and it only half took. (3) Palette: this is warm amber almost throughout, with none of the world plate's cold blue-green damp; the room's own atmosphere text calls for dark brown tile and one failing lamp string, so it may be in-spec for this room, but it sits differently from the rest of the collection. Also note for wiring: the gall barrels are two, not three, and the weld aft cab's doorway is a dark slot rather than a lit interior, so its hotspot box will be the least legible of the four doors.

## parked (1)

### saffron_hill — 3 attempt(s)
- attempt cap (3) spent without clearing the gates

## ungenerated (1)

### logwood_quay — 2 attempt(s)

## unknown (7)

### car_lampblack — 0 attempt(s)

### car_madder — 0 attempt(s)

### car_verdigris — 0 attempt(s)

### car_weld — 0 attempt(s)

### ochre_hall — 0 attempt(s)

### ochre_verdigris — 0 attempt(s)

### ochre_woad — 0 attempt(s)

NONE OF THESE ARE ACCEPTED. `hold` means the still survived every automatic gate and needs Lucas's eye; metrics screen out, they cannot certify. Read the Concerns first — that is where the loop recorded what it was unsure of.