#!/usr/bin/env python3
"""briggs_bers_pinch.py

Briggs–Bers pinch-point (absolute/convective) analysis for a parallel wake profile
using the inviscid Rayleigh equation (inviscid Orr–Sommerfeld).

Theory sketch
-------------
We consider the spatio-temporal dispersion relation D(α, ω) = 0, where
  ω = α c(α)
and c(α) is an eigenvalue (phase speed) of the Rayleigh problem for complex α.

A pinch/saddle point α0 is defined by
  D(α0, ω0)=0  AND  dω/dα(α0)=0
The absolute growth rate is Im(ω0):
  - Im(ω0) > 0 => absolute instability
  - Im(ω0) < 0 => convective instability

Implementation strategy
-----------------------
1) Build U(y) from a slice x≈x0 of a Tecplot-style .dat file.
2) For any complex α, solve Rayleigh EVP and compute ω eigenvalues.
3) Select a single analytic branch ω(α) by continuation (closest-to-previous ω).
4) Find α0 such that dω/dα = 0 using a 2-real-variable root solve for α = ar+i ai.

Important caveats
-----------------
- Pinch-point analysis is subtle: branch tracking matters. This code uses a simple
  continuation heuristic (nearest ω). It works best if started near the saddle.
- Domain truncation and interpolation quality matter (Rayleigh assumes parallel flow).
- Rayleigh equation is inviscid; for some profiles the spectrum can be sensitive.

Usage
-----
python briggs_bers_pinch.py \
  --dat /path/to/Re11K_DNS.dat \
  --x0 0.6 --tol 5e-4 \
  --alpha0 1.9+0.0j \
  --N 220 \
  --h 1e-3

Outputs a report and writes a JSON with the found saddle.
"""

from __future__ import annotations

import argparse
import json
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
        raise RuntimeError(f"No points found with |x-x0|<=tol. x0={x0}, tol={tol}")

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


def omega_branch(Ufun, alpha: complex, N: int, ymin: float, ymax: float, omega_prev: complex | None):
    """Compute ω(α) for one tracked branch.

    If omega_prev is None: pick the eigenvalue with max Im(ω).
    Else: pick eigenvalue closest to omega_prev.
    """
    y, c, omega = rayleigh_temporal(Ufun, alpha, N=N, ymin=ymin, ymax=ymax)
    if omega.size == 0:
        raise RuntimeError("No finite eigenvalues returned")

    if omega_prev is None:
        j = int(np.argmax(np.imag(omega)))
        return omega[j]

    j = int(np.argmin(np.abs(omega - omega_prev)))
    return omega[j]


def domega_dalpha(Ufun, alpha: complex, N: int, ymin: float, ymax: float, omega_prev: complex | None, h: float):
    """Complex derivative dω/dα via centered finite difference along real axis.

    For analytic ω(α), this approximates the complex derivative.
    We use continuation to keep the same branch.
    """
    a1 = alpha - h
    a2 = alpha + h

    w1 = omega_branch(Ufun, a1, N, ymin, ymax, omega_prev)
    w2 = omega_branch(Ufun, a2, N, ymin, ymax, omega_prev)
    return (w2 - w1) / (2.0 * h), w1, w2


def parse_complex(s: str) -> complex:
    # allow forms like 1.9+0.1j
    return complex(s.replace(" ", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", required=True, type=Path)
    ap.add_argument("--x0", required=True, type=float)
    ap.add_argument("--tol", default=5e-4, type=float)
    ap.add_argument("--N", default=220, type=int)
    ap.add_argument("--y-pad", default=0.0, type=float)
    ap.add_argument("--alpha0", default="1.9+0.0j", type=str)
    ap.add_argument("--h", default=1e-3, type=float, help="FD step for dω/dα")
    ap.add_argument("--out", default=Path("pinch_result.json"), type=Path)
    args = ap.parse_args()

    alpha0 = parse_complex(args.alpha0)

    x_mean, y_prof, U_prof = extract_profile(args.dat, args.x0, args.tol)
    Ufun = make_Ufun(y_prof, U_prof)

    ymin = float(y_prof[0] - args.y_pad)
    ymax = float(y_prof[-1] + args.y_pad)

    print(f"Profile slice: x≈{args.x0} (mean x={x_mean:.8f}), Ny={len(y_prof)}")
    print(f"y in [{ymin:.6f}, {ymax:.6f}], U in [{U_prof.min():.6f}, {U_prof.max():.6f}]")

    # Initial ω guess from most unstable temporal mode at alpha0
    w0 = omega_branch(Ufun, alpha0, args.N, ymin, ymax, omega_prev=None)
    print(f"Initial guess: alpha0={alpha0}, omega0={w0}")

    # Root solve for F(ar,ai) = [Re(dω/dα), Im(dω/dα)] = 0
    # We use a lightweight continuation of omega_prev by re-evaluating ω at each α.

    def F(z):
        ar, ai = z
        a = ar + 1j * ai

        # choose omega_prev as ω(a) from previous call? scipy doesn't provide state.
        # Instead, use ω(alpha0) as a reference for branch selection; this is usually
        # OK if the solver stays near the saddle.
        omega_ref = w0

        dw, _, _ = domega_dalpha(Ufun, a, args.N, ymin, ymax, omega_prev=omega_ref, h=args.h)
        return np.array([dw.real, dw.imag], dtype=float)

    z0 = np.array([alpha0.real, alpha0.imag], dtype=float)

    sol = root(F, z0, method="hybr", tol=1e-10)

    if not sol.success:
        print("Root solve did not converge:")
        print(sol.message)

    ar, ai = sol.x
    alpha_star = ar + 1j * ai

    # Evaluate ω at saddle (using branch near w0)
    omega_star = omega_branch(Ufun, alpha_star, args.N, ymin, ymax, omega_prev=w0)

    # classify
    classification = "absolute" if omega_star.imag > 0 else "convective"

    report = {
        "dat": str(args.dat),
        "x0": args.x0,
        "tol": args.tol,
        "x_mean": x_mean,
        "Ny": int(len(y_prof)),
        "ymin": ymin,
        "ymax": ymax,
        "N_cheb": args.N,
        "alpha_init": [alpha0.real, alpha0.imag],
        "omega_init": [w0.real, w0.imag],
        "alpha_star": [alpha_star.real, alpha_star.imag],
        "omega_star": [omega_star.real, omega_star.imag],
        "Im_omega_star": float(omega_star.imag),
        "classification": classification,
        "root_success": bool(sol.success),
        "root_message": str(sol.message),
        "root_nfev": int(sol.nfev),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    print("\n=== Pinch-point result ===")
    print(f"alpha* = {alpha_star}")
    print(f"omega* = {omega_star}")
    print(f"Im(omega*) = {omega_star.imag:.6e}  => {classification} instability")
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
