#!/usr/bin/env python3
from pathlib import Path
import numpy as np
from scipy.interpolate import LinearNDInterpolator
import re

SRC = Path('/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/Re5K_DNS.dat')
OUT = Path('/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/Re5K_DNS_xy_regular.dat')
XMIN, XMAX, DX = 0.6, 3.0, 0.02
YMIN, YMAX, DY = -5.0, 5.0, 0.02

node_count = None
rows = []
with SRC.open() as f:
    for line in f:
        s = line.strip()
        if s.startswith('ZONE'):
            mN = re.search(r'N=(\d+)', s)
            if mN:
                node_count = int(mN.group(1))
            continue
        if not s or s[0].isalpha() or s[0] in ('"', '#'):
            continue
        parts = s.split()
        try:
            vals = [float(x) for x in parts]
        except ValueError:
            continue
        if node_count is not None and len(rows) < node_count and len(vals) >= 8:
            rows.append(vals[:8])
        elif node_count is not None and len(rows) >= node_count:
            break

arr = np.array(rows, dtype=float)
xy = arr[:, :2]
U = arr[:, 3]
V = arr[:, 4]
W = arr[:, 5]
P = arr[:, 6]
T = arr[:, 7]
Zconst = float(np.median(arr[:, 2]))

print(f'loaded nodes: {arr.shape[0]}  z~{Zconst}')

xu = np.arange(XMIN, XMAX + 0.5 * DX, DX)
yu = np.arange(YMIN, YMAX + 0.5 * DY, DY)
Xg, Yg = np.meshgrid(xu, yu, indexing='xy')
pts = np.column_stack([Xg.ravel(), Yg.ravel()])

interp_U = LinearNDInterpolator(xy, U, fill_value=np.nan)
interp_V = LinearNDInterpolator(xy, V, fill_value=np.nan)
interp_W = LinearNDInterpolator(xy, W, fill_value=np.nan)
interp_P = LinearNDInterpolator(xy, P, fill_value=np.nan)
interp_T = LinearNDInterpolator(xy, T, fill_value=np.nan)

Ug = interp_U(pts)
Vg = interp_V(pts)
Wg = interp_W(pts)
Pg = interp_P(pts)
Tg = interp_T(pts)

mask = np.isfinite(Ug) & np.isfinite(Vg) & np.isfinite(Wg) & np.isfinite(Pg) & np.isfinite(Tg)
pts = pts[mask]
Ug = Ug[mask]
Vg = Vg[mask]
Wg = Wg[mask]
Pg = Pg[mask]
Tg = Tg[mask]

with OUT.open('w') as f:
    f.write('TITLE = "Re5K_DNS_xy_regular"\n')
    f.write('VARIABLES = "X" "Y" "Z" "U" "V" "W" "P" "T"\n')
    f.write(f'ZONE T="xy_regular", N={len(pts)}, E=0, DATAPACKING=POINT, ZONETYPE=FETRIANGLE\n')
    for (x, y), u, v, w, p, t in zip(pts, Ug, Vg, Wg, Pg, Tg):
        f.write(f'{x:.9e} {y:.9e} {Zconst:.9e} {u:.9e} {v:.9e} {w:.9e} {p:.9e} {t:.9e}\n')

print(f'wrote {OUT} with {len(pts)} points')
