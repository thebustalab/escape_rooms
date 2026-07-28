---
authority: intent
---

# Solve / door-open sounds — per-gate plan (2026-07-21)

Each puzzle solve (and each escape lock releasing) can play a one-shot `solveSfx` the moment the door
opens. Sound is matched to the door the room's *forward* scene actually opens (read off each room's
`authoring.doorPrompt`). Candidates are staged in each scenario's `_scratch/audio/` named
`solve_<roomKey>_<gateId>_<n>.mp3`; the puzzle editor (`puzzle_edit.html`) lists the two candidates per
gate for audition + one-click "Use this" (materialises into `audio/` and sets `solveSfx`).

## Gate → door type

**Alaska — `data_vis/alaska` ("Signal in the Cold"), an Arctic research station**
- `room1` the_dispatch_laptop — **heavy wooden door** (interior)
- `room2` the_kitchen_table_laptop — **heavy wooden door** (interior)
- `room3` a_still_glowing_laptop — **heavy wooden door** (interior)
- `boss` the_workbench_laptop — **heavy exterior door → wind/snow** (helicopter rotors beyond)
- `escape1` the_keypad_panel (lock) — **helicopter passenger hatch** opening

**Hawai'i — `data_vis/Hawaii` ("Saltwater Intrusion"), field lab + wellheads**
- `room1` the_lab_laptop — **heavy wooden door** (to night porch)
- `room2` the_field_laptop — **creaky wooden gate** (mossy jungle gate)
- `room3` the_colleague_s_laptop — **steel access hatch** flipping open (metal + ladder)
- `boss` the_valve_keypad (lock) + the_waterproof_laptop (puzzle) — **metal valve/control-panel** sliding open

**Airship — `data_vis2/airship` ("The Astrolabe"), a steampunk airship (brass-and-teal)**
- `room1` obj_test — **riveted iron door** (funnel-lock drained → clank/steam)
- `room2` obj_test — **deck hatch** flipping open (brass ship hatch)
- `room3` obj_test — **heavy bulk door** onto a companionway
- `boss` obj_test — **great metal bulkhead** grinding open
- `captain` obj_lock (lock) — **ornate brass door**

**Hospital — `data_vis2/hospital` ("Vital Signs"), a sunny hospital**
- `room1` the_bench_laptop — **elevator door** sliding open (brushed steel)
- `room2` the_phone_in_the_wall_clip — **elevator doors + ding** (into corridor)
- `room3` the_nurses_station_laptop — **swinging interior door** (lab door)
- `boss` the_lab_workstation_laptop — **swinging interior door** (to break room)
- `escape1` the_keypad_on_the_door (lock) — **door out to the sunny car park** (the way out)

## Distinct sound types (2 candidates each, shared across same-type gates)

wooden_door · exterior_door_wind · heli_hatch · wooden_gate_creak · metal_hatch · valve_panel ·
iron_door_steam · metal_bulkhead · brass_door · elevator_door · swing_door · exit_door

Sources: freesound.org, Creative Commons (all CC0 — these ship on the public site). Pulled through the
**`sound_pull` observer project** (`Utilities/sound_pull/`) — write a `{url,dest}` spec and submit a
`sound_pull` row; the persistent observer downloads them so a Claude session teardown can't orphan the pull
(which it did, repeatedly, on the first attempt). Candidate pool is gitignored `_scratch`; only the picked,
materialised `audio/*.mp3` ships.

## The 24 freesound sources (CC0), by type

- wooden_door — Ryding/125958, piedo/214693
- exterior_door_wind — deleted_user_7146007/383830, Garuda1982/633122
- heli_hatch — craigsmith/438732 (submarine hatch), Irolan/488221 (small metal hatch) · the one helicopter
  clip found had an unknown licence and was dropped for a CC0 hatch
- wooden_gate_creak — WavJunction.com/456763, RealSquink/788015
- metal_hatch — Rudmer_Rotteveel/718445, Irolan/488221
- valve_panel — magnuswaker/530075, SpliceSound/369869
- iron_door_steam — kyles/407323, + a heavy-metal-door reuse (EpicWizard/264889 kept timing out, dropped)
- metal_bulkhead — ALEFF-ATMOS/452784, kyles/637583
- brass_door — kyles/407304, ValentinPetiteau/564393
- elevator_door — T.I.B/788698, buzzatsea/427109
- swing_door — kyles/453974, squareal/237403
- exit_door — Anthousai/398749, LamaMakesMusic/403536

