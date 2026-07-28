#!/usr/bin/env python3
"""Recover the invisible watermark from a downloaded escape-room figure.

The player (shared/pano-player.js -> embedWatermark) LSB-encodes a payload into the RED channel
of every pixel, row-major, as a repeating frame:  MAGIC("ESRW") + length(1 byte) + UTF-8 payload,
with the bits written MSB-first. The payload is  x500|scenario|epoch_ms .

Usage:
    python3 decode_watermark.py figure.png            # prints the payload
    python3 decode_watermark.py figure.png --json      # prints parsed fields as JSON

Needs Pillow (pip install pillow). PNG is lossless, so the LSBs survive a plain download; a
re-encode to JPEG or a heavy edit will destroy them (this is an obfuscation speed-bump, not a
tamper-proof control — see escape_rooms/AGENTS.md).
"""
import sys
import json
from PIL import Image

MAGIC = b"ESRW"


def decode(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    # red LSB of every pixel, row-major (matches the canvas getImageData order)
    bits = [px[x, y][0] & 1 for y in range(h) for x in range(w)]
    # pack MSB-first into bytes
    by = bytearray()
    for i in range(0, len(bits) - 7, 8):
        v = 0
        for b in range(8):
            v = (v << 1) | bits[i + b]
        by.append(v)
    # scan for the MAGIC frame header, then read length + payload
    for i in range(len(by) - 5):
        if by[i:i + 4] == MAGIC:
            n = by[i + 4]
            if i + 5 + n <= len(by):
                try:
                    return by[i + 5:i + 5 + n].decode("utf-8")
                except UnicodeDecodeError:
                    continue
    return None


def _embed(im, payload):
    """Python port of shared/pano-player.js embedWatermark — MUST stay bit-for-bit identical to it
    (red LSB, row-major, MAGIC+len(1)+UTF-8 payload, bits MSB-first, frame repeated). Used only by
    --selftest; if the JS scheme changes, change this and re-run the self-test (cf. the codec's R
    self-test / JS-vs-Python check)."""
    w, h = im.size
    px = im.load()
    b = list(payload.encode("utf-8"))[:255]
    frame = list(MAGIC) + [len(b)] + b
    bits = [(byte >> i) & 1 for byte in frame for i in range(7, -1, -1)]
    bi = 0
    for y in range(h):
        for x in range(w):
            r, g, bl, a = px[x, y]
            px[x, y] = ((r & 0xFE) | bits[bi % len(bits)], g, bl, a)
            bi += 1
    return im


def selftest():
    import io
    ok = True
    for payload in ["bust0037", "smit1234|hawaii_aquifers|1721170000000", "x", "a" * 200 + "|z|9"]:
        im = Image.new("RGBA", (200, 150))
        for y in range(150):
            for x in range(200):
                im.putpixel((x, y), ((x * 7) % 256, (y * 5) % 256, (x + y) % 256, 255))
        _embed(im, payload)
        buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
        got = decode(buf)
        good = got == payload
        ok &= good
        print(("PASS" if good else "FAIL"), repr(payload[:28]), "->", repr((got or "")[:28]))
    print("SELFTEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    as_json = "--json" in sys.argv
    if not args:
        sys.exit("usage: python3 decode_watermark.py figure.png [--json]  |  --selftest")
    payload = decode(args[0])
    if payload is None:
        sys.exit("no watermark found (image may be re-encoded/edited, or was never marked)")
    if as_json:
        parts = payload.split("|")
        out = {"x500": parts[0] if parts else "",
               "scenario": parts[1] if len(parts) > 1 else "",
               "epoch_ms": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None}
        print(json.dumps(out))
    else:
        print(payload)


if __name__ == "__main__":
    main()
