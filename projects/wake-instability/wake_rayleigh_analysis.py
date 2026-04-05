#!/usr/bin/env python3
"""wake_rayleigh_analysis.py

Extract wake profile U(y) at x = x0 from a Tecplot-style .dat file and run
Rayleigh (inviscid Orr–Sommerfeld) temporal stability analysis using
rayleigh_chebyshev.py.

This produces a *temporal* instability scan over alpha (real streamwise wavenumber):
- compute most unstable omega for each alpha
- report max growth rate and corresponding phase speed c

NOTE:
- This is a temporal (convective-amplifier style) analysis.
- Absolute vs convective classification requires a Briggs–Bers pinch-point search
  in complex k/omega; not implemented here.

Usage:
  python wake_rayleigh_analysis.py \
    --dat /path/to/Re11K_DNS.dat \
    --x0 0.6 \
    --tol 1e-4 \
    --alpha-min 0.1 --alpha-max 3.0 --alpha-n 40

Outputs:
  - wake_profile_x0.600000.csv
  - rayleigh_scan_x0.600000.csv
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

# rayleigh solver from the workspace file
from rayleigh_chebyshev import rayleigh_temporal


def iter_numeric_rows(path: Path, ncols: int = 11):
    """Yield numeric rows (float arrays) from a Tecplot-ish .dat file.

    Skips header lines like TITLE/VARIABLES/ZONE/DT and blank lines.
    Assumes each data row has at least ncols floats.
    """
    with path.open("r", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            c0 = s[0]
            if c0.isalpha() or c0 in ('"', '#'):
                continue
            # try parse floats
            parts = s.split()
            if len(parts) < ncols:
                continue
            try:
                vals = [float(parts[i]) for i in range(ncols)]
            except ValueError:
                continue
            yield np.array(vals, dtype=float)


def extract_profile(dat_path: Path, x0: float, tol: float):
    """Extract (y, U) points at x≈x0."""
    ys = []
    Us = []
    xs = []

    for row in iter_numeric_rows(dat_path, ncols=11):
        x, y, u = row[0], row[1], row[2]
        if abs(x - x0) <= tol:
            xs.append(x)
            ys.append(y)
            Us.append(u)

    if not ys:
        raise RuntimeError(
            f"No points found with |x-x0|<=tol. x0={x0}, tol={tol}. "
            f"Try increasing tol or inspect x-range/unique x values."
        )

    xs = np.asarray(xs)
    ys = np.asarray(ys)
    Us = np.asarray(Us)

    # If there are duplicate y's (multiple points share y), average U at each y.
    # Use rounding to group near-identical y values.
    ykey = np.round(ys, decimals=8)
    uniq = np.unique(ykey)
    y_out = np.empty_like(uniq)
    U_out = np.empty_like(uniq)
    for i, yk in enumerate(uniq):
        mask = ykey == yk
        y_out[i] = np.mean(ys[mask])
        U_out[i] = np.mean(Us[mask])

    # sort by y
    idx = np.argsort(y_out)
    y_out = y_out[idx]
    U_out = U_out[idx]

    # Return also mean x actually found
    return float(np.mean(xs)), y_out, U_out


def linear_interp_fun(y_data: np.ndarray, U_data: np.ndarray):
    """Return a callable U(y) using linear interpolation with flat extrapolation."""
    y0 = float(y_data[0])
    y1 = float(y_data[-1])

    def Ufun(y):
        y = np.asarray(y, dtype=float)
        U = np.interp(y, y_data, U_data)
        # np.interp does flat extrapolation automatically at ends
        return U

    return Ufun, y0, y1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", required=True, type=Path)
    ap.add_argument("--x0", required=True, type=float)
    ap.add_argument("--tol", default=1e-4, type=float)
    ap.add_argument("--N", default=220, type=int, help="Chebyshev intervals")
    ap.add_argument("--y-pad", default=0.0, type=float, help="Extend y-domain beyond min/max of data")
    ap.add_argument("--alpha-min", default=0.1, type=float)
    ap.add_argument("--alpha-max", default=6.0, type=float)
    ap.add_argument("--alpha-n", default=100, type=int)
    ap.add_argument("--outdir", default=Path("."), type=Path)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    x_mean, y_prof, U_prof = extract_profile(args.dat, args.x0, args.tol)
    print(f"Extracted {len(y_prof)} unique y points at x≈{args.x0} (mean x={x_mean:.8f})")
    print(f"y range: [{y_prof[0]:.6f}, {y_prof[-1]:.6f}]")
    print(f"U range: [{U_prof.min():.6f}, {U_prof.max():.6f}]")

    prof_csv = args.outdir / f"wake_profile_x{args.x0:.6f}.csv"
    with prof_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_mean", x_mean])
        w.writerow(["y", "U"])
        for yi, Ui in zip(y_prof, U_prof):
            w.writerow([f"{yi:.10e}", f"{Ui:.10e}"])
    print(f"Wrote profile: {prof_csv}")

    Ufun, ymin_data, ymax_data = linear_interp_fun(y_prof, U_prof)

    ymin = ymin_data - args.y_pad
    ymax = ymax_data + args.y_pad

    alphas = np.linspace(args.alpha_min, args.alpha_max, args.alpha_n)

    rows = []
    best = None

    for alpha in alphas:
        ygrid, c, omega = rayleigh_temporal(Ufun, float(alpha), N=args.N, ymin=float(ymin), ymax=float(ymax))
        # take the most unstable mode (sorted by imag(omega) desc)
        c0 = c[0]
        w0 = omega[0]
        rows.append((alpha, c0.real, c0.imag, w0.real, w0.imag))

        if best is None or (w0.imag > best[4]):
            best = (alpha, c0.real, c0.imag, w0.real, w0.imag)

        print(f"alpha={alpha:.4f}  omega={w0.real:+.6f}{w0.imag:+.6f}i")

    scan_csv = args.outdir / f"rayleigh_scan_x{args.x0:.6f}.csv"
    with scan_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "c_real", "c_imag", "omega_real", "omega_imag"])
        for r in rows:
            w.writerow([f"{r[0]:.10e}", f"{r[1]:.10e}", f"{r[2]:.10e}", f"{r[3]:.10e}", f"{r[4]:.10e}"])
    print(f"Wrote scan: {scan_csv}")

    if best is not None:
        alpha, cr, ci, wr, wi = best
        print("\nMost unstable (temporal) among scanned alphas:")
        print(f"  alpha = {alpha:.6f}")
        print(f"  c     = {cr:+.6e}{ci:+.6e}i")
        print(f"  omega = {wr:+.6e}{wi:+.6e}i")
        if wi > 0:
            print(f"  --> temporally unstable (growth rate Im(omega)={wi:.3e})")
        else:
            print(f"  --> temporally stable over scanned alpha range")


if __name__ == "__main__":
    main()
