# DiT360 / FLUX.1-dev — prompting & tuning notes

Working reference for generating the escape-room 360 panoramas (FLUX.1-dev +
DiT360 LoRA, run via `~/dit360_bench/` harness). Distilled from the FLUX docs +
community guides (2026) and our own runs.

## The one big idea: seed and prompt do *different* jobs

- **Prompt = what's in the image** (objects, style, mood).
- **Seed = the specific instantiation** — composition, placement, and how
  *coherently* it renders. The "AI-mush / disjointed objects" problem is
  **seed-driven**, not prompt-complexity-driven (confirmed in our seed sweep).
- Rule of thumb: *a bad prompt isn't saved by the right seed, and the right seed
  won't fix a bad prompt.* Get the content right with the prompt; get a clean
  render by seed-hunting.

## The workflow ("seed hunting")

1. **Sweep seeds** on a fixed prompt → find compositions that render cleanly.
2. **Lock the winning seed**, then **iterate the prompt** to refine content/detail
   (FLUX holds the rough composition stable across small prompt edits at a fixed
   seed). This is the professional loop: *lock seed, adjust prompt, iterate*.
3. Keep steps/guidance fixed while doing the above (so changes are attributable).
4. **Upscale/detail pass last**, on the chosen winner only.

## Good levels

| Lever | Good range | Notes |
|---|---|---|
| **Steps** | **28** (24–32) | Sweet spot for FLUX.1-dev. Beyond ~30–40 = diminishing returns; 50 ≈ 28. Don't burn time here. |
| **Guidance** | **2.8–3.8** | FLUX "guidance" ≠ SD CFG. 3.0–3.8 is the general FLUX sweet spot; **DiT360 defaults to 2.8** (panorama LoRA likes it softer). Worth testing 2.8 vs ~3.5 — let the images decide. **Never** go 7+ (SD habit) → oversaturated, artifacty. |
| **Resolution** | **fixed 2048×1024** | DiT360 only trained here; other sizes misbehave. Not a lever. |

## What sort of prompts (FLUX ≠ Stable Diffusion / Midjourney)

- **Natural language, full sentences** — describe the scene to a person. NOT
  comma-separated tags. Keyword-stuffing hurts.
- **Detailed is good** — ~80–150 words. FLUX follows long, story-like direction.
- **Front-load the important elements.** FLUX weights earlier words more — and for
  us *doubly so*: FLUX's CLIP encoder truncates at **77 tokens** (only T5 sees the
  whole prompt), so put the key content in the first ~60 words, atmosphere later.
- **Drop quality-tag filler** ("masterpiece, 8k, highly detailed") — near-useless
  in FLUX; it already biases to quality.
- **No SD weighting syntax** (`(word:1.3)`). Use natural emphasis: "with the laptop
  as the focal point."
- **Avoid "white background"**-type phrases (can wash out edges).
- **DiT360 requirement:** the prompt must **start with `This is a panorama.`**

## Improved cabin prompt (front-loaded, natural, ~90 words)

> This is a panorama. A 360-degree view from the centre of a warm, lamplit
> log-cabin search-and-rescue station at night. Ahead stands a sturdy wooden desk
> with a single open laptop below a large topographic lake map on the log wall.
> Around the room: a cork board with a few pinned notes, a cast-iron wood stove
> with a kettle, a heavy closed wooden door with a storm lantern, and a wide window
> onto a dark frozen lake. Tidy and uncluttered, warm amber light against cool blue
> night, calm muted palette. No people.

(vs the original, which front-loaded nothing and padded the end with filler that
CLIP never saw anyway.)
