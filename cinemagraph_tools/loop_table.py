#!/usr/bin/env python3
"""For every viewer clip, tabulate the best loop junction at each minimum loop length.

Answering Lucas: yes, you can measure how similar all frames are and cut where they match best.
But it is a TRADE, not a free win - the best-matching pair is usually a SHORT loop, and the
improvement varies hugely by clip (measured: quay control 6.7x -> 3.9x at best; dev Z1 5.5x ->
1.6x, i.e. nearly seamless). So the viewer gets a slider over this table rather than one answer.

Cost = static (do the frames look alike) + 0.5 * dynamic (is the motion going the same way).
Distances are normalised by the mean ADJACENT-frame difference, so "1.0x" means the junction is as
smooth as any ordinary frame step - a perfect loop - and is comparable across clips.
"""
import os, subprocess, json
import numpy as np
from PIL import Image

UI = ("/home/bustalab/Documents/Tools/websites/thebustalab.github.io/escape_rooms/"
      "authoring_v2/ui/cine360")
SCALE = 4          # 768x256: keeps real detail, and the pair matrix stays small


def frames(mp4):
    d = "/tmp/sweep/_lt"; subprocess.run(["rm", "-rf", d], check=False); os.makedirs(d)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf",
                    f"scale=iw/{SCALE}:ih/{SCALE}", f"{d}/%04d.png"], check=True)
    fs = sorted(os.listdir(d))
    a = np.stack([np.asarray(Image.open(os.path.join(d, f)).convert("L"), dtype=np.float32)
                  for f in fs])
    subprocess.run(["rm", "-rf", d], check=False)
    return a.reshape(len(fs), -1)


def table(flat):
    n = len(flat)
    # row by row: the full broadcast would be n*n*pixels and needs tens of GB
    D = np.empty((n, n), dtype=np.float32)
    for i in range(n):
        D[i] = np.abs(flat - flat[i]).mean(axis=1)
    adj = float(np.mean([D[k, k+1] for k in range(n-1)]))
    C = D.copy()
    C[:n-1, :n-1] += 0.5 * D[1:, 1:]          # dynamic term: next frames must match too
    C[n-1, :] += 0.5 * D.max(); C[:, n-1] += 0.5 * D.max()
    out = []
    for pct in (100, 90, 80, 70, 60, 50, 40, 30, 25):
        minlen = max(8, int(n * pct / 100) - 1)
        best = None
        for i in range(n):
            for j in range(i + minlen, n):
                if best is None or C[i, j] < best[0]:
                    best = (float(C[i, j]), i, j)
        if best is None: continue
        _, i, j = best
        out.append(dict(pct=pct, i=i, j=j, frames=j - i + 1,
                        ratio=round(float(D[i, j]) / adj, 2)))
    return out, adj, round(float(D[0, n-1]) / adj, 2), n, round(float(D[0, n-1]), 2)


if __name__ == "__main__":
    res = {}
    for f in sorted(os.listdir(UI)):
        if not f.endswith(".mp4") or f.endswith("_boom.mp4"): continue
        try:
            t, adj, now, n, absj = table(frames(os.path.join(UI, f)))
        except Exception as e:
            print(f"{f}: FAILED {e}"); continue
        res[f] = dict(n=n, now=now, abs_jump=absj, adjacent=round(adj,2), table=t)
        best = min(t, key=lambda r: r["ratio"])
        print(f"{f:<30} {n:3d}f  as-is {now:5.1f}x   best {best['ratio']:4.1f}x "
              f"({best['frames']}f = {best['frames']/24:.2f}s, cut {best['i']}->{best['j']})")
    json.dump(res, open("/tmp/sweep/loop_table.json", "w"), indent=1)
    print("\n-> /tmp/sweep/loop_table.json")
