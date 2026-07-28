#!/usr/bin/env python3
"""
make_map.py — regenerate the escape "survey chart" from the real data.

Renders the UNLABELLED pH x Calcium scatter of all 20 Alaska lakes (map.png) plus map_points.json
(a clickable hit-box per lake, in image-fraction coords) that the pano-player `map` puzzle reads. The
chart is deliberately unlabelled: the player recreates it with geom_text to find their lake, then clicks
its point (answer = Imuruk_Lake, the lowest-pH lake in the BELA / Bering Land Bridge aquifer).

Axes are pH x Ca because they separate all 20 lakes best (min normalised spacing 0.054) and are
decoupled from the crush's constraint, so the label-reveal is forced. Deterministic — same CSV in, same
PNG + boxes out. Run:  python3 make_map.py   (needs matplotlib). Regenerate after any data change and
re-run ../test_hospital.py.
"""
import csv, json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

def find_csv():
    """Walk up to the site root and locate the shared sample dataset."""
    d = HERE
    for _ in range(8):
        cand = os.path.join(d, "phylochemistry", "sample_data", "alaska_lake_data.csv")
        if os.path.exists(cand):
            return cand
        d = os.path.dirname(d)
    raise FileNotFoundError("alaska_lake_data.csv not found above " + HERE)

def main():
    rows = list(csv.DictReader(open(find_csv(), encoding="utf-8")))
    num = lambda x: float(x) if x not in ("", "NA") else None
    lakes = sorted(set(r["lake"] for r in rows))
    ph, ca = {}, {}
    for r in rows:
        ph[r["lake"]] = num(r["pH"])
        if r["element"] == "Ca":
            ca[r["lake"]] = num(r["mg_per_L"])

    W, H, D = 8.0, 8.0, 100                      # 800x800 px
    fig = plt.figure(figsize=(W, H), dpi=D)
    fig.patch.set_facecolor("#06111a")
    ax = fig.add_axes([0.12, 0.10, 0.84, 0.86])
    ax.set_facecolor("#0a1620")
    ax.scatter([ph[l] for l in lakes], [ca[l] for l in lakes],
               s=150, facecolor="#8fd6ff", edgecolor="#dff2ff", linewidth=1.3, zorder=3, alpha=0.95)
    ax.set_xlabel("pH", color="#cfe6f2", fontsize=15)
    ax.set_ylabel("Calcium (mg/L)", color="#cfe6f2", fontsize=15)
    ax.tick_params(colors="#7f97a6")
    for s in ax.spines.values():
        s.set_color("#24384a")
    ax.grid(True, color="#162432", alpha=0.5, linewidth=0.6)
    fig.savefig(os.path.join(HERE, "map.png"), dpi=D, facecolor=fig.get_facecolor())

    fig.canvas.draw()
    Wpx, Hpx, half = W * D, H * D, 18            # 36px hit-boxes
    pts = []
    for l in lakes:
        px, py = ax.transData.transform((ph[l], ca[l]))
        fx, fyt = px / Wpx, 1 - py / Hpx
        bw, bh = half / Wpx, half / Hpx
        pts.append({"lake": l, "box": [round(fx - bw, 4), round(fyt - bh, 4), round(fx + bw, 4), round(fyt + bh, 4)]})
    json.dump({"axes": {"x": "pH", "y": "Ca"}, "image": "map.png", "points": pts},
              open(os.path.join(HERE, "map_points.json"), "w"), indent=2)
    print("wrote map.png + map_points.json (%d lakes)" % len(pts))

if __name__ == "__main__":
    main()
