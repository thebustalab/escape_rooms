I checked the clip and the art myself.

**The worker is right that the clip is dead.** My own region measurement on the raw render: the tarn's temporal variation (5.5% of its mean) sits *below* the static left crag (11.1%) and the static platform rock (7.1%), and the whole-frame difference from frame 0 climbs monotonically to its peak at the last frame — slow global drift, not cyclic flow. Five frames cropped to the tarn are visually identical: same reflection boundary, same ice floes, no cat's-paws. So this is the dead reading, and it wasn't reached from the zero return alone.

**But the proposed fix is wrong, and it's wrong in a checkable way.** I opened both images:

- rooms/networks/beacons/rams_head/scene.png — the committed, human-accepted panorama (Lucas, 2026-09-03) — contains **no lantern**. No gibbet arm, no hook, nothing just left of centre but rock and tarn.
- notes/reauthor/beacons__rams_head.candidate.png — the re-authoring experiment the lantern prompt belongs to — is a **completely different panorama**: different peaks, a visible sun flare, a wet platform, and yes, a brass lantern on an iron arm. That is the image Lucas watched move. It was never committed.

So the worker has conflated two different pictures. Authoring a swinging lantern into this room's spec puts an object in the motion prompt that is not in the frame being animated — exactly the phantom-object state cycle 8 identified and removed. The only way to make the lantern real is to regenerate and re-commit the art, which discards a human-accepted seam and writes into committed art.

Two supporting claims also don't survive checking. The committed scenePrompt *does* carry the tarn's vigour — "its black surface crossed by slow travelling cat's-paws of wind that darken and silver it" — so "no vigour ever written into the art" is false; and the motionSpec already has tarn_surface as a boxed hero subject with its own phrase. Cycle 8 read the pair the right way round.

The clip is dead because the committed art depicts a glassy mirror-still tarn with nothing to animate — that's a genuine finding and it deserves a human eye on what mover this panorama can actually support. It is not a licence to reinstate an object from a different image.

VERDICT: FAIL