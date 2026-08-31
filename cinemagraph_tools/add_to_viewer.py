#!/usr/bin/env python3
"""Add clips to the 360 test viewer: copy, build the motion map, and register in the menu.

Wiring a clip in by hand is four fiddly steps (copy the mp4, copy the right source still, generate
the motion map, edit the JSON in the HTML) and I have got it slightly wrong more than once. This
does all four from one command.

  add_to_viewer.py <room> <clip.mp4> [more.mp4 ...] --label "prefix"

`room` is the Egypt room key, used to find the correct source still — the still MUST match the clip
or the masked composite silently blends two different scenes.
"""
import os, sys, json, re, shutil, argparse, fcntl
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion_mask import sample_frames

UI = "/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/authoring_v2/ui"
EGY = "/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/rooms/wrangling/egypt"
MOTION_SCALE = 40.0


def ensure_still(room, night=False):
    src = f"{EGY}/{room}/{'scene_night.png' if night else 'scene.png'}"
    dst_name = f"{room}{'_night' if night else ''}_source_still.png"
    dst = f"{UI}/cine360/{dst_name}"
    if not os.path.isfile(dst):
        shutil.copy2(src, dst)
    return f"cine360/{dst_name}"


def motion_map(clip_path, out_name):
    """Regenerate whenever the clip is NEWER than its map. Skipping on mere existence left the
    re-run AA clips wearing motion maps built from the earlier, invalid renders — the mask in the
    viewer then describes a video that no longer exists."""
    out = f"{UI}/cine360/{out_name}"
    stale = (not os.path.isfile(out)) or os.path.getmtime(clip_path) > os.path.getmtime(out)
    if stale:
        fr = sample_frames(clip_path, n=16)
        tstd = fr.std(axis=0).mean(axis=2)
        Image.fromarray((np.clip(tstd / MOTION_SCALE, 0, 1) * 255).astype(np.uint8), "L").save(out)
        pct = {p: float(np.percentile(tstd, p)) for p in (50, 90, 99)}
        print(f"    motion map: median {pct[50]:.1f}  p90 {pct[90]:.1f}  p99 {pct[99]:.1f}")
    return f"cine360/{out_name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("room")
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--label", default="")
    ap.add_argument("--night", action="store_true")
    ap.add_argument("--page", default="cine360_test.html",
                    help="which viewer page to register in")
    a = ap.parse_args()

    still = ensure_still(a.room, a.night)
    page = f"{UI}/{a.page}"
    # Hold an exclusive lock across read-modify-write. Two writers to this file (the watcher and a
    # hand edit to the player) silently lost one side's changes: the wrap-flash marker and the
    # longer crossfade were both overwritten seconds after being added, because the watcher had
    # read the page before the edit and wrote it back after.
    lock = open(f"/tmp/sweep/.viewer_{a.page}.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    s = open(page).read()
    m = re.search(r'window\.__CLIPS__ = (\[.*?\]);', s, re.S)
    clips = json.loads(m.group(1))
    have = {c["url"] for c in clips}

    for c in a.clips:
        base = os.path.splitext(os.path.basename(c))[0]
        dst = f"{UI}/cine360/{base}.mp4"
        if os.path.abspath(c) != os.path.abspath(dst):
            shutil.copy2(c, dst)
        url = f"cine360/{base}.mp4"
        print(f"  {base}")
        entry = {"url": url, "label": (a.label + " " if a.label else "") + base,
                 "still": still, "motion": motion_map(dst, base + "_motion.png")}
        clips = [x for x in clips if x["url"] != url] + [entry]

    new = "window.__CLIPS__ = " + json.dumps(clips) + ";"
    s = re.sub(r'window\.__CLIPS__ = \[.*?\];', lambda _: new, s, flags=re.S)
    tmp = page + ".tmp"
    open(tmp, "w").write(s)
    os.replace(tmp, page)               # atomic: never leave a half-written page on disk
    fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
    print(f"registered {len(clips)} clips in the viewer")


main()
