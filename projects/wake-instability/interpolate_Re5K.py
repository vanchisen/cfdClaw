#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import numpy as np
from scipy.interpolate import griddata


def iter_numeric_rows(path: Path, ncols: int = 11):
    with path.open('r', errors='ignore') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            c0 = s[0]
            if c0.isalpha() or c0 in ('"', '#'):
                continue
            parts = s.split()
            if len(parts) < ncols:
                continue
            try:
                vals = [float(parts[i]) for i in range(ncols)]
            except ValueError:
                continue
            yield vals


def read_numeric_array(path: Path, ncols: int = 11) -> np.ndarray:
    arr = np.array(list(iter_numeric_rows(path, ncols=ncols)), dtype=float)
    if arr.size == 0:
        raise RuntimeError(f'No numeric rows parsed from {path}')
    return arr


def main():
    ap = argparse.ArgumentParser(description='Interpolate Re5K_DNS.dat onto the regular XY grid pattern of Re11K_DNS_xy_regular.dat')
    ap.add_argument('--src', default=Path('/users/zwang197/Works/NeuroSEM/WakeInstability/Re5K_DNS.dat'), type=Path,
                    help='Source irregular Tecplot-style DNS file')
    ap.add_argument('--template', default=Path('/users/zwang197/Works/NeuroSEM/WakeInstability/Re11K_DNS_xy_regular.dat'), type=Path,
                    help='Template regular-grid file providing target (x,y) pattern')
    ap.add_argument('--out', default=Path('/users/zwang197/Works/NeuroSEM/WakeInstability/Re5K_DNS_xy_regular.dat'), type=Path,
                    help='Output regular-grid Tecplot-style point file')
    ap.add_argument('--method', default='linear', choices=['linear', 'nearest', 'cubic'],
                    help='Primary interpolation method for scipy.interpolate.griddata')
    args = ap.parse_args()

    src = read_numeric_array(args.src, ncols=11)
    tmpl = read_numeric_array(args.template, ncols=11)

    xy_src = src[:, 0:2]
    xy_tgt = tmpl[:, 0:2]

    out = np.zeros((xy_tgt.shape[0], 11), dtype=float)
    out[:, 0:2] = xy_tgt

    # interpolate all remaining columns onto the template XY grid
    for j in range(2, 11):
        vals = src[:, j]
        interp = griddata(xy_src, vals, xy_tgt, method=args.method)

        # fill any NaNs outside convex hull using nearest-neighbor fallback
        mask = np.isnan(interp)
        if np.any(mask):
            interp[mask] = griddata(xy_src, vals, xy_tgt[mask], method='nearest')

        out[:, j] = interp

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w') as f:
        f.write('TITLE = "Re5K_DNS_xy_regular"\n')
        f.write('VARIABLES = "X" "Y" "U" "V" "W" "P" "uu" "vv" "ww" "uv" "pp"\n')
        for row in out:
            f.write(' '.join(f'{v:.9e}' for v in row) + '\n')

    print(f'Read source:    {args.src} ({src.shape[0]} points)')
    print(f'Read template:  {args.template} ({tmpl.shape[0]} target points)')
    print(f'Wrote output:   {args.out}')
    print(f'Interpolation:  method={args.method} with nearest fallback for NaNs')


if __name__ == '__main__':
    main()
