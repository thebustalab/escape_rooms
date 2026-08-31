#!/usr/bin/env python3
"""Rebuild a sibling 360 viewer page from cine360_test.html, keeping that page's own clip list.

A sibling page is a COPY of the test viewer, so every improvement to the player (loop modes, seam
repair, the wrap-flash marker) otherwise has to be applied twice and drifts apart. This makes the
test page the single source of truth for the PLAYER, and each sibling page just a clip list.

  sync_viewer.py                                  -> rebuilds cine360_endguide.html (default)
  sync_viewer.py cine360_night.html "Night rooms"  -> rebuilds/creates any sibling page

Creating a page this way starts it with an empty clip list, which is the point: register clips into
it with `add_to_viewer.py --page <that page>` rather than hand-editing the HTML.
"""
import re, json, sys

UI = ("/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/"
      "authoring_v2/ui")
SRC = f"{UI}/cine360_test.html"
DST = f"{UI}/{sys.argv[1]}" if len(sys.argv) > 1 else f"{UI}/cine360_endguide.html"
TITLE = sys.argv[2] if len(sys.argv) > 2 else "Cinemagraph 360 — end-guide sweep"

clips = []
try:
    d = open(DST).read()
    clips = json.loads(re.search(r'window\.__CLIPS__ = (\[.*?\]);', d, re.S).group(1))
except Exception as e:
    print("no existing endguide clip list:", e)

s = open(SRC).read()
s = s.replace("<title>Cinemagraph 360 test</title>", f"<title>{TITLE}</title>")
s = re.sub(r'window\.__CLIPS__ = \[.*?\];',
           lambda _: "window.__CLIPS__ = " + json.dumps(clips) + ";", s, flags=re.S)
open(DST, "w").write(s)
print(f"{DST.rsplit('/', 1)[-1]} rebuilt from the test viewer, {len(clips)} clips kept")
