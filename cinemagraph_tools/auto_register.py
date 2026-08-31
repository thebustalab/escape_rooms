#!/usr/bin/env python3
"""Watch the render output folders and wire any NEW clip into the 360 viewer as it appears.

Lucas: "as other things land, add them too." Until now clips were registered in a batch at the end
of a stage, so a four-render stage showed nothing for over an hour. This polls instead, so each
clip appears in the menu the moment it is fetched.

Per clip it does what add_to_viewer.py does (copy, matching source still, motion map, menu entry)
and then builds the boomerang file, so every loop mode works on it immediately.

Stops when /tmp/sweep/STOP_WATCH exists, or after MAX_HOURS.
"""
import os, sys, time, json, subprocess, glob

TEMP = "/home/bustalab/Documents/Tools/temp"
# Menu labels say what each clip is FOR, so the dropdown itself tells Lucas what to compare.
LABELS = {
  "AB1": "F1. BOATS boat-first prompt (vs D) --",
  "AB2": "F2. BOATS cfg 4.5          (vs D) --",
  "AB3": "F3. BOATS looser end-guide (vs D) --",
  "AB4": "F4. DISTILLED pinned still (vs D) - the sharpness confound --",
  "AC1": "G1. END 1.0 no mask   (vs A) --",
  "AC2": "G2. END 2.0 no mask   (vs A) --",
  "AC3": "G3. END 1.0 + PIN MASK (vs A) - loop fix, water free --",
  "AC4": "G4. END 2.0 + PIN MASK (vs A) --",
  "AD1": "H1. end-guide 0.30 (vs A=0.6) --",
  "AD2": "H2. end-guide 0.45 (vs A=0.6) --",
  "AD3": "H3. end-guide 0.70 (vs A=0.6) --",
  "AD4": "H4. end-guide 1.50 (vs A=0.6) --",
  "AD5": "H5. end-guide 3.00 (vs A=0.6) --",
  "AE1": "J1. end 1.0 + MASK v2 (fixed) --",
  "AE2": "J2. end 2.0 + MASK v2 (fixed) --",
  "AE3": "J3. end 0.6 + MASK v2 - masking alone, motion unchanged? --",
  "AF1": "K1. 97f @3072 end1.0 - long + hard pin --",
  "AF2": "K2. 121f @2048 end1.0 --",
  "AF3": "K3. 169f @1536 end1.0 - longest + hard pin --",
  "AF4": "K4. 169f @1536 end0.6 - same length, normal pin --",
  "AG1": "L1. 73f end0.7 + mask --",
  "AG2": "L2. 73f end0.8 + mask --",
  "AG3": "L3. 73f end0.9 + mask --",
  "AG4": "M1. 97f end0.7 + mask - full res, longer --",
  "AG5": "M2. 97f end0.8 + mask - full res, longer --",
  "AG6": "M3. 97f end0.9 + mask - full res, longer --",
  "AH1": "L5. 73f end1.1 + mask --",
  "AH2": "L6. 73f end1.2 + mask --",
  "AH3": "L7. 73f end1.3 + mask --",
  "AI1": "H3a. 73f end0.80 NO mask --",
  "AI2": "H3b. 73f end0.90 NO mask --",
  "AK1": "P1. prompt +SKY (gulls, clouds) --",
  "AK2": "P2. prompt +CLOTH/FLAME --",
  "AK3": "P3. prompt +EVERYTHING --",
}
SWEEP = "/tmp/sweep"
MAX_HOURS = 8
POLL = 45


def room_of(dirname):
    """The room decides which source still the mask composites against; a mismatch silently blends
    two different scenes, so guess conservatively and skip what we cannot identify."""
    base = os.path.basename(dirname)
    if base.startswith("quay_"): return "quay"
    if base.startswith("merchant_"): return "merchant"
    return None


# The end-guide sweep gets its OWN page: Lucas asked not to have it buried among the earlier
# experiments. Everything else keeps going to the main test viewer.
ENDGUIDE_PAGE = "cine360_endguide.html"
def page_for(name):
    return ENDGUIDE_PAGE if name.startswith(("AC", "AD", "AE", "AF", "AG", "AH", "AI", "AK", "AB4")) else "cine360_test.html"


UI = ("/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/"
      "authoring_v2/ui")


def registered_urls():
    """Basenames already present in EITHER viewer page.

    Seeding from the filesystem was wrong: on restart every existing render looked "already
    handled", so clips that landed while the watcher was down (AD1-AD3) were never registered and
    never would be. The viewer pages are the real record of what has been wired up."""
    import re
    out = set()
    for page in ("cine360_test.html", ENDGUIDE_PAGE):
        try:
            s = open(f"{UI}/{page}").read()
            m = re.search(r'window\.__CLIPS__ = (\[.*?\]);', s, re.S)
            for c in json.loads(m.group(1)):
                out.add(os.path.splitext(os.path.basename(c["url"]))[0])
        except Exception:
            pass
    return out


def register(room, path, label):
    base0 = os.path.splitext(os.path.basename(path))[0]
    page = page_for(base0)
    r = subprocess.run([sys.executable, f"{SWEEP}/add_to_viewer.py", room, path,
                        "--label", label, "--page", page],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print(("  + " if ok else "  ! ") + f"[{page}] " + os.path.basename(path) +
          ("" if ok else " -- " + r.stderr.strip()[-200:]), flush=True)
    if ok:
        base = os.path.splitext(os.path.basename(path))[0]
        subprocess.run([sys.executable, f"{SWEEP}/make_boomerang.py", base],
                       capture_output=True, text=True)
    return ok


def main():
    watch = sys.argv[1:] or sorted(glob.glob(f"{TEMP}/quay_*") + glob.glob(f"{TEMP}/merchant_*"))
    seen = registered_urls()
    print(f"watching {len(watch)} folders; {len(seen)} clips already in the viewers", flush=True)
    t0 = time.time()
    while time.time() - t0 < MAX_HOURS * 3600:
        if os.path.exists(f"{SWEEP}/STOP_WATCH"):
            print("stop requested", flush=True); break
        for d in watch:
            room = room_of(d)
            if not room: continue
            for p in sorted(glob.glob(f"{d}/*.mp4")):
                rp = os.path.splitext(os.path.basename(p))[0]
                if rp in seen: continue
                # only once ffmpeg/the fetch has finished writing it
                s1 = os.path.getsize(p); time.sleep(2)
                if os.path.getsize(p) != s1 or s1 == 0: continue
                seen.add(rp)
                register(room, p, LABELS.get(os.path.splitext(os.path.basename(p))[0],
                             os.path.basename(d).replace("quay_", "").upper()[:12]))
        time.sleep(POLL)
    print("watcher done", flush=True)


main()
