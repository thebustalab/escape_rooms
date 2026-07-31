#!/usr/bin/env python3
"""
build_metabolomics.py — (re)generate + verify the hospital scenario's teaching dataset.

Writes the two LONG-format CSVs the scenario uses:
  phylochemistry/sample_data/metabolomics_hospital.csv          (20 patients × 10 metabolites)
  phylochemistry/sample_data/metabolomics_hospital_unknown.csv  (patient "Elias")

The eight non-engineered metabolites are REAL values pulled from phylochemistry/sample_data/
metabolomics_data.csv (first 10 healthy + first 10 kidney_disease patients). Two elements are
ENGINEERED (see phylochemistry/sample_data/AGENTS.md):
  - indoxyl sulfate / p-cresyl sulfate: a Simpson's-paradox pair (strong pooled, ~0 within group);
  - Elias: patient 54's near-twin + a big creatinine spike (one clean room-2 match; one clear boss marker).

Deterministic (fixed seeds). Re-run after any change, then re-run test_hospital.py. Requires numpy;
prints a verification of all four puzzle rungs. Paths are relative to the repo root.
"""
import csv, os, numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "phylochemistry", "sample_data", "metabolomics_data.csv")
K = os.path.join(ROOT, "phylochemistry", "sample_data", "metabolomics_hospital.csv")
U = os.path.join(ROOT, "phylochemistry", "sample_data", "metabolomics_hospital_unknown.csv")

MET = ['Choline', '2-Aminoisobutyric acid', 'Creatinine', 'Methylmalonate', 'myoinositol',
       'Hydroxyphenylpyruvic acid', '1-Methyladenosine', 'Pyruvate', 'Indoxyl_Sulfate', 'p_Cresyl_Sulfate']
REAL = MET[:8]                                       # the eight real-valued metabolites
BOSS = ['Creatinine', 'Methylmalonate', 'myoinositol', 'Hydroxyphenylpyruvic acid', '1-Methyladenosine']
ROOM2 = [m for m in MET if m != 'Creatinine']       # heatmap panel (renal assay "pending")

def main():
    np.random.seed(11)
    src = list(csv.DictReader(open(SRC)))
    st = np.array([r['patient_status'] for r in src])
    cv = lambda m: np.array([np.nan if src[i][m] in ('NA', '') else float(src[i][m]) for i in range(len(src))])
    Xa = {m: cv(m) for m in REAL}
    ih = [i for i, s in enumerate(st) if s == 'healthy'][:10]
    ik = [i for i, s in enumerate(st) if s == 'kidney_disease'][:10]
    sel = ih + ik
    V = {m: Xa[m][sel] for m in REAL}
    pn = [src[i]['patient_number'] for i in sel]
    g = [st[i] for i in sel]
    hidx = [k for k in range(20) if g[k] == 'healthy']
    hmean = {m: V[m][hidx].mean() for m in REAL}
    hsd = {m: V[m][hidx].std() for m in REAL}
    np.random.seed(11)
    V['Indoxyl_Sulfate'] = np.array([(10.0 if g[k] == 'healthy' else 14.0) + np.random.normal(0, 0.5) for k in range(20)])
    V['p_Cresyl_Sulfate'] = np.array([(10.0 if g[k] == 'healthy' else 14.0) + np.random.normal(0, 0.5) for k in range(20)])
    tw = pn.index('54')
    elias = {m: V[m][tw] + (0 if m == 'Creatinine' else np.random.normal(0, 0.05 * (hsd.get(m) or V[m].std()))) for m in MET}
    elias['Creatinine'] = hmean['Creatinine'] + 6.0 * hsd['Creatinine']   # unambiguous outlier (cohort max)

    with open(K, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['patient_number', 'patient_status', 'metabolite', 'concentration'])
        for k in range(20):
            for m in MET:
                w.writerow([pn[k], g[k], m, f"{V[m][k]:.3f}"])
    with open(U, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['patient_number', 'metabolite', 'concentration'])
        for m in MET:
            w.writerow(['Elias', m, f"{elias[m]:.3f}"])
    print("wrote:", os.path.relpath(K, ROOT), "+", os.path.relpath(U, ROOT))

    # verification
    KW = {}
    for r in csv.DictReader(open(K)):
        KW.setdefault(r['patient_number'], {'patient_status': r['patient_status']})[r['metabolite']] = float(r['concentration'])
    UW = {r['metabolite']: float(r['concentration']) for r in csv.DictReader(open(U))}
    ids = list(KW); gg = np.array([KW[i]['patient_status'] for i in ids]); C = lambda m: np.array([KW[i][m] for i in ids])
    rr = lambda a, b, mk=None: np.corrcoef(*((a, b) if mk is None else (a[mk], b[mk])))[0, 1]
    a, b = C('Choline'), C('2-Aminoisobutyric acid')
    print(f"ROOM1 Choline~2AIB pooled {rr(a,b):.2f} H {rr(a,b,gg=='healthy'):.2f} K {rr(a,b,gg=='kidney_disease'):.2f}")
    sx, sy = C('Indoxyl_Sulfate'), C('p_Cresyl_Sulfate')
    print(f"ROOM3 Simpson pooled {rr(sx,sy):.2f} H {rr(sx,sy,gg=='healthy'):.2f} K {rr(sx,sy,gg=='kidney_disease'):.2f}")
    M = np.array([[KW[i][m] for m in ROOM2] for i in ids]); mu, sd = M.mean(0), M.std(0); Z = (M - mu) / sd
    ez = np.array([(UW[m] - mu[j]) / sd[j] for j, m in enumerate(ROOM2)])
    dist = sorted((np.linalg.norm(ez - Z[k]), ids[k]) for k in range(20))
    print(f"ROOM2 nearest {dist[0][1]} d={dist[0][0]:.2f}; 2nd {dist[1][1]} d={dist[1][0]:.2f}; margin {dist[1][0]-dist[0][0]:.2f}")
    z = sorted(((UW[m] - hmean.get(m, C(m).mean())) / (hsd.get(m) or C(m).std()), m) for m in BOSS)[::-1]
    print(f"BOSS  winner {z[0][1]} (z={z[0][0]:+.1f} vs healthy); Elias creatinine is cohort max: {UW['Creatinine']>C('Creatinine').max()}")

if __name__ == "__main__":
    main()
