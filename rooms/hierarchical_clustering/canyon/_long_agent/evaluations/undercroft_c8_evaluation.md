The worker was right to hold, and I checked the clip myself rather than relying on their account.

- **The clip is new.** `undercroft_motion_ri6_looped.mp4` was written at 23:00 on 2026-09-17, after the 22:48 still that already shows the ripples. It was rendered at seed 4242, 3072×1024, 61 frames.
- **The frames look right.** Across the sampled frames the camera doesn't move and the hall stays fixed: the bronze flood door, the steps, the piers, the map table, the control panel, the ladder and the arch. In the left pool, the rings and the amber lamplight streaks shift between frame 0 and frame 30. So the motion stays inside the pool and matches the spec's `motion.phrase`, with the door, steps and piers staying still as the spec asks. I saw no tearing and no stray motion anywhere else.
- **The gate report agrees.** Glitch breadth is 0.021 normalised, the dead-clip ratio is 15.74 and return is 0.05, so there's no ambiguous zero-return case to weigh. One small mismatch: the report counts 73 glitch frames, but the looped clip has 61. That doesn't affect the decision.
- **None of the reject conditions apply.** It doesn't propose any settings change or a new mover. It doesn't accept the clip or write anything into `scenario.json`. It explicitly says holding is not acceptance, so the clip just waits for Lucas to look at it.

VERDICT: PASS