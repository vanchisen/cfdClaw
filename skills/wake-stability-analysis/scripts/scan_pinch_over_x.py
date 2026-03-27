#!/usr/bin/env python3
"""scan_pinch_over_x.py

Scan x locations, extract wake profile U(y) at each x, perform a Briggs–Bers
pinch-point search (Rayleigh equation) and report Im(omega*) vs x.

This is a *spatio-temporal* absolute/convective analysis (complex alpha, omega).

Because pinch-point searches are sensitive to initialization/branch tracking,
this script uses a small multi-start set of initial guesses for alpha.

Outputs:
  - pinch_scan.csv (x_mean, Im(omega*), omega*, alpha*, classification, flags)
  - prints best (most unstable) x in the scanned range.

Example:
  python scan_pinch_over_x.py \
    --dat /path/Re11K_DNS.dat \
    --x-min 0.55 --x-max 1.5 --x-step 0.05 \
    --tol 5e-4 --N 180 --h 1e-3 \
    --outdir ./re11k_pinch_scan
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import root

from rayleigh_chebyshev import rayleigh_temporal


def iter_numeric_rows(path: Path, ncols: int = 11):
    with path.open("r", errors="ignore") as f:
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
            yield np.array(vals, dtype=float)


def extract_profile(dat_path: Path, x0: float, tol: float):
    ys, Us, xs = [], [], []
    for row in iter_numeric_rows(dat_path, ncols=11):
        x, y, u = row[0], row[1], row[2]
        if abs(x - x0) <= tol:
            xs.append(x)
            ys.append(y)
            Us.append(u)

    if not ys:
        return None

    xs = np.asarray(xs)
    ys = np.asarray(ys)
    Us = np.asarray(Us)

    # group near-identical y values and average U
    ykey = np.round(ys, 8)
    uniq = np.unique(ykey)
    y_out = np.empty_like(uniq)
    U_out = np.empty_like(uniq)
    for i, yk in enumerate(uniq):
        m = (ykey == yk)
        y_out[i] = np.mean(ys[m])
        U_out[i] = np.mean(Us[m])

    idx = np.argsort(y_out)
    y_out = y_out[idx]
    U_out = U_out[idx]

    return float(np.mean(xs)), y_out, U_out


def make_Ufun(y_data: np.ndarray, U_data: np.ndarray):
    def Ufun(y):
        y = np.asarray(y, dtype=float)
        return np.interp(y, y_data, U_data)

    return Ufun


def omega_branch(Ufun, alpha: complex, N: int, ymin: float, ymax: float, omega_ref: complex | None):
    y, c, omega = rayleigh_temporal(Ufun, alpha, N=N, ymin=ymin, ymax=ymax)
    if omega.size == 0:
        raise RuntimeError("No finite eigenvalues")

    if omega_ref is None:
        j = int(np.argmax(np.imag(omega)))
        return omega[j]

    j = int(np.argmin(np.abs(omega - omega_ref)))
    return omega[j]


def domega_dalpha(Ufun, alpha: complex, N: int, ymin: float, ymax: float, omega_ref: complex, h: float):
    w1 = omega_branch(Ufun, alpha - h, N, ymin, ymax, omega_ref)
    w2 = omega_branch(Ufun, alpha + h, N, ymin, ymax, omega_ref)
    return (w2 - w1) / (2 * h)


@dataclass
class PinchResult:
    ok: bool
    x_mean: float
    Ny: int
    alpha_star: complex | None
    omega_star: complex | None
    im_omega: float | None
    classification: str | None
    msg: str
    nfev: int | None


def pinch_search(Ufun, ymin, ymax, N, h, alpha_init: complex) -> PinchResult:
    # reference omega from max growth at alpha_init
    try:
        omega_ref = omega_branch(Ufun, alpha_init, N, ymin, ymax, omega_ref=None)
    except Exception as e:
        return PinchResult(False, np.nan, 0, None, None, None, None, f"omega_ref_fail: {e}", None)

    def F(z):
        a = z[0] + 1j * z[1]
        try:
            dw = domega_dalpha(Ufun, a, N, ymin, ymax, omega_ref=omega_ref, h=h)
        except Exception:
            # penalize failures
            return np.array([1e6, 1e6], dtype=float)
        return np.array([dw.real, dw.imag], dtype=float)

    z0 = np.array([alpha_init.real, alpha_init.imag], dtype=float)
    sol = root(F, z0, method="hybr", tol=1e-10)

    alpha_star = sol.x[0] + 1j * sol.x[1]
    try:
        omega_star = omega_branch(Ufun, alpha_star, N, ymin, ymax, omega_ref=omega_ref)
    except Exception as e:
        return PinchResult(False, np.nan, 0, alpha_star, None, None, None, f"omega_star_fail: {e}", int(sol.nfev))

    classification = "absolute" if omega_star.imag > 0 else "convective"

    # We consider it OK if the function norm is small, even if solver.success is False.
    fnorm = float(np.linalg.norm(sol.fun))
    ok = sol.success or fnorm < 1e-4
    msg = f"success={sol.success} fnorm={fnorm:.2e} {sol.message}".strip()

    return PinchResult(ok, np.nan, 0, alpha_star, omega_star, float(omega_star.imag), classification, msg, int(sol.nfev))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", required=True, type=Path)
    ap.add_argument("--x-min", type=float, default=0.55)
    ap.add_argument("--x-max", type=float, default=1.5)
    ap.add_argument("--x-step", type=float, default=0.05)
    ap.add_argument("--tol", type=float, default=5e-4)
    ap.add_argument("--N", type=int, default=180)
    ap.add_argument("--h", type=float, default=1e-3)
    ap.add_argument("--y-pad", type=float, default=0.0)
    ap.add_argument("--outdir", type=Path, default=Path(".") )
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    out_csv = args.outdir / "pinch_scan.csv"

    x_targets = np.arange(args.x_min, args.x_max + 0.5 * args.x_step, args.x_step)

    # multi-start initial guesses (tuned around the temporal most-unstable alpha~1.9)
    alpha_inits = [
        1.6 + 0.00j,
        1.9 + 0.00j,
        2.2 + 0.00j,
        1.9 + 0.05j,
        1.9 - 0.05j,
    ]

    rows = []
    best = None

    for x0 in x_targets:
        prof = extract_profile(args.dat, float(x0), args.tol)
        if prof is None:
            print(f"x0={x0:.3f}: no points found")
            rows.append((x0, np.nan, 0, "", "", "", "no_points"))
            continue

        x_mean, y_prof, U_prof = prof
        Ufun = make_Ufun(y_prof, U_prof)
        ymin = float(y_prof[0] - args.y_pad)
        ymax = float(y_prof[-1] + args.y_pad)

        Ny = len(y_prof)

        # run multi-start pinch; pick the one with largest Im(omega*) among acceptable results
        best_here = None
        for a0 in alpha_inits:
            r = pinch_search(Ufun, ymin, ymax, args.N, args.h, a0)
            r.x_mean = x_mean
            r.Ny = Ny
            if (best_here is None) or (r.omega_star is not None and best_here.omega_star is not None and r.omega_star.imag > best_here.omega_star.imag and r.ok):
                best_here = r
            elif best_here is None and r.omega_star is not None:
                best_here = r

        r = best_here
        if r is None or r.omega_star is None:
            print(f"x≈{x_mean:.6f}: pinch failed")
            rows.append((x_mean, np.nan, Ny, "", "", "", "pinch_failed"))
            continue

        print(f"x≈{x_mean:.6f}: Im(omega*)={r.omega_star.imag:+.4e}  alpha*={r.alpha_star}  {r.classification}  {r.msg}")

        rows.append((
            x_mean,
            r.omega_star.imag,
            Ny,
            f"{r.alpha_star.real:+.8e}{r.alpha_star.imag:+.8e}j",
            f"{r.omega_star.real:+.8e}{r.omega_star.imag:+.8e}j",
            r.classification,
            r.msg.replace("\n", " "),
        ))

        if r.ok:
            if best is None or r.omega_star.imag > best.omega_star.imag:
                best = r

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_mean", "Im_omega_star", "Ny", "alpha_star", "omega_star", "classification", "note"])
        for row in rows:
            w.writerow(row)

    print(f"\nWrote: {out_csv}")

    if best and best.omega_star is not None:
        print("\n=== Most unstable (max Im(omega*)) among scanned x ===")
        print(f"x_mean = {best.x_mean:.8f}")
        print(f"alpha*  = {best.alpha_star}")
        print(f"omega*  = {best.omega_star}")
        print(f"Im(omega*) = {best.omega_star.imag:.6e} ({best.classification})")
    else:
        print("\nNo successful pinch results found in scan.")


if __name__ == "__main__":
    main()
