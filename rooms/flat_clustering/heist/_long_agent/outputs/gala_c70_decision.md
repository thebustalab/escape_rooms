I read all four documents, then verified the room's actual state rather than trusting the brief's empty history.

**What I found on disk.** This room has already been through the fix — the brief's `What was tried already: []` is wrong, and four cycles (c52–c55) died on a permission-rule error without deciding anything.

- **The art was re-authored and regenerated.** `scenario.json.bak_..._gala_reauthor` at 22:01 on 09-13, `scene.png` rewritten at 22:24. The still is *newer* than the spec edit, so art and spec agree — no `needs_still` block.
- **The still depicts the mover.** I opened the left-of-centre third at native resolution. The house pennant is there exactly as authored: navy silk on a varnished staff, streaming out near-horizontal against open sky, the free end curling over on itself, the halyard visibly bowed. Bounded — a narrow slice of frame, high contrast against sky — and hanging/streaming cloth is the ledger's strongest confirmed mover category.
- **The dead drapes are correctly neutralised.** They now carry only the legacy `animate` block, which the motion machinery cannot see, and they are named in the spec's `rigid` string, ready for the escalation if they misbehave.
- **`render_motion_prompt` gives one clean single-mover prompt**: *"locked-off static camera, zero camera movement. The single silk house pennant on its staff streaming and rippling in the dawn breeze, its free end curling and snapping over. Only that moves; everything else stays perfectly still. Seamless natural loop."* "Motion prompt: NONE" just means no `art_prompt_motion/` fallback file — correct, the spec is the source of truth.
- **The stale-prompt note carried forward from c32/c34 is resolved.** The regenerated `scenePrompt` carries the EQUIRECT clause, the seam anchor at head and tail, style and edge discipline — it came from `render_prompt`.
- **No clip exists for this art.** The only clip, `gala_motion_ri32_looped.mp4`, rendered at 21:23 — an hour *before* the new still. It is a clip of the drapes panorama Lucas called dead, not of this one.

The art fix has already been made and never rendered. Nothing here calls for re-authoring, and softening or pinning without a clip would be tuning against a defect that hasn't appeared.

```
DECISION: RENDER
WHY: The re-authored spec declares one bounded mover whose depicted vigour gpt-image-2.5 visibly honoured in a scene.png newer than the spec edit, render_motion_prompt yields a correct single-mover house-form prompt, and the only existing clip predates that still by an hour — so no clip exists for this room's current art.
```

One thing for the record, not acted on: the pennant's vigour clause appears twice in the art prompt, once inside the authored `desc` and once appended by `render_prompt` from `motion.vigour`. It is duplicated emphasis rather than a defect, and the still it produced is right — but the `desc` should shed its vigour wording if this room is ever re-authored again.