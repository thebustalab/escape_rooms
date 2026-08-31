#!/usr/bin/env python3
"""Build a ping-pong (boomerang) copy of each viewer clip: forward, then backward, as one file.

Why a FILE rather than JS: reversing in the browser means either seeking backwards every frame
(h264 has few keyframes, so it stutters badly) or caching every decoded frame (3072x1024 RGBA x 73
frames is ~900 MB). A prebuilt file plays back as smoothly as the original and needs no new logic
in the viewer beyond swapping the source.

The turnaround frames are dropped from the reversed half, otherwise the first and last frames each
show twice and the motion visibly hesitates at both ends.
"""
import os, subprocess, sys, json

UI = ("/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/"
      "authoring_v2/ui/cine360")


def nframes(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                          "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(out.split(",")[0])


def boomerang(src, dst):
    n = nframes(src)
    # reversed half keeps frames 1..n-2, so neither turnaround frame is duplicated
    fc = (f"[0:v]split=2[a][b];"
          f"[b]reverse,select='between(n\\,1\\,{n-2})',setpts=N/FRAME_RATE/TB[r];"
          f"[a][r]concat=n=2:v=1[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
                    "-map", "[out]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    dst], check=True)
    return n, nframes(dst)


if __name__ == "__main__":
    names = sys.argv[1:] or [f[:-4] for f in sorted(os.listdir(UI))
                             if f.endswith(".mp4") and not f.endswith("_boom.mp4")]
    for base in names:
        src = f"{UI}/{base}.mp4"; dst = f"{UI}/{base}_boom.mp4"
        if not os.path.isfile(src):
            print(f"  {base}: no source"); continue
        if os.path.isfile(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
            print(f"  {base}: up to date"); continue
        try:
            a, b = boomerang(src, dst)
            print(f"  {base}: {a} -> {b} frames  ({os.path.getsize(dst)/1e6:.0f} MB)")
        except subprocess.CalledProcessError as e:
            print(f"  {base}: FFMPEG FAILED {e}")
