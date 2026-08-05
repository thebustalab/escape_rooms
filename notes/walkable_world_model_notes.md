---
authority: intent
---

# Walkable "world-model" scenes (explored 2026-07-17, not started)

Parked exploration, relocated from `escape_rooms/AGENTS.md` → Known follow-ups on 2026-08-05 to keep the
hub lean. Not started; revisit if we want to move beyond look-around-from-one-spot rooms.

Lucas asked how hard it would be to move from look-around-from-one-spot rooms to Street-View-style
*walking through* a continuous space. Findings:

- Real Google Street View is the wrong tool (Google's imagery of real places only, API keys/cost, can't
  render invented scenes) though its overlay API would keep hotspots working.
- Stitching several AI panoramas together (Blockade Labs Skybox AI etc.) hits exactly the continuity
  problem — similar-but-disjoint bubbles that feel like teleporting.
- The real answer is the current **"world model"** generation crop — **World Labs' Marble**, Spline's
  **Spell**, Echo-2/Spaitial — which build ONE continuous explorable 3D volume (as **Gaussian splats**)
  from a single image/prompt and render live in the browser via **Three.js** (World Labs' open-source
  **Spark** lib; mobile-capable). Sweet spot is **room-sized** worlds — which fits an escape *room* almost
  perfectly; going bigger means composing several and the seams return.
- Cost of adopting: swap **Pannellum → Three.js/Spark** (different renderer), rework hotspots as 3D markers
  placed in the scene (arguably nicer — they sit on objects, not on a sphere), and accept the softer,
  dreamier splat look vs the crisp gpt-image-2 stills. Puzzles/WebR layer is renderer-agnostic and carries
  over untouched.
- Next step if pursued: a one-image Marble proof-of-concept with a single working hotspot in the browser,
  to judge look + feel before committing.
