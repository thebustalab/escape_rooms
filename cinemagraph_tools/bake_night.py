#!/usr/bin/env python3
"""Bake the five night clips to flat, phone-watchable loops with Lucas's 0.5 s crossfade.

Numbering continues the existing mobile_previews series (the daytime work ended at 21), so the
night set is 22-26 and nothing already on his phone shifts underneath him.

No mask composite here: these are the BASE renders and the question on the table is whether the
recipe transfers, which means he should see what the model actually produced. Masking is a
separate lever and would hide exactly the drift we are trying to judge.
"""
import os, subprocess, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
NIGHT = "/home/bustalab/Documents/Tools/temp/egypt_night"
PREV = "/home/bustalab/Documents/Tools/temp/mobile_previews"
os.makedirs(PREV, exist_ok=True)

# order chosen for viewing, not alphabetically: the two that should be easy first, then the two
# hard cases, then the fire.
ORDER = [("22", "deck"), ("23", "boat"), ("24", "hold"), ("25", "pharos"), ("26", "lantern"),
         # the night VARIANTS of the seven day rooms (found 2026-08-31)
         ("27", "deck_night"), ("28", "quay_night"), ("29", "emporion_night"),
         ("30", "market_price_night"), ("31", "market_boast_night"), ("32", "canopic_night"),
         ("33", "library_night")]

for num, room in ORDER:
    src = f"{NIGHT}/{room}.mp4"
    if not os.path.isfile(src):
        print(f"  {room:<10} SKIP — no render at {src}")
        continue
    out = (f"{PREV}/{num}_{room}.mp4" if room.endswith("_night")
           else f"{PREV}/{num}_{room}_night.mp4")
    subprocess.run([sys.executable, f"{TOOLS}/bake_flat.py", src, "--out", out,
                    "--fade", "0.5", "--fps", "24"], check=True)
    print(f"  {room:<10} -> {out}  ({os.path.getsize(out)/1e6:.1f} MB)")

print("\nBaked. All are 3072x1024 with a 0.5 s crossfade, no mask.")
