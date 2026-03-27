#!/usr/bin/env python3
"""verify_triantafyllou_re140k.py

Verification run using the analytic wake profile fit used in
Triantafyllou, Triantafyllou & Chryssostomidis (JFM 1986), eq. (14),
for Re=140000.

Paper statements to compare against (symmetric mode):
- At x/d = 1.0: absolute instability; critical point approx
    omega_R ~ 1.3, omega_I ~ 0.087
    k_R ~ 2.2, k_I ~ -1.75
- At x/d = 2.0: convective instability.

Their fitted profile (eq. 14):
  U(y)/U0 = 1 - A + A*tanh( a*((y/d)^2 - b) )

Here we set d=1, U0=1 (non-dimensional).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import root

from rayleigh_chebyshev import rayleigh_temporal


def U_profile_factory(A: float, a: float, b: float):
    def U(y):
        y = np.asarray(y, dtype=float)
        return 1.0 - A + A * np.tanh(a * (y**2 - b))
    return U


def omega_branch(Ufun, alpha: complex, N: int, ymin: float, ymax: float, omega_ref: complex | None):
    _, c, omega = rayleigh_temporal(Ufun, alpha, N=N, ymin=ymin, ymax=ymax)
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
class Result:
    label: str
    A: float
    a: float
    b: float
    alpha_star: complex
    omega_star: complex
    success: bool
    fnorm: float
    message: str


def pinch(Ufun, N=220, ymin=-6.0, ymax=6.0, h=1e-3, alpha_init=2.2-1.7j):
    omega_ref = omega_branch(Ufun, alpha_init, N, ymin, ymax, omega_ref=None)

    def F(z):
        alpha = z[0] + 1j*z[1]
        try:
            dw = domega_dalpha(Ufun, alpha, N, ymin, ymax, omega_ref, h)
            return np.array([dw.real, dw.imag], dtype=float)
        except Exception:
            return np.array([1e6, 1e6], dtype=float)

    z0 = np.array([alpha_init.real, alpha_init.imag], dtype=float)
    sol = root(F, z0, method="hybr", tol=1e-11)
    alpha_star = sol.x[0] + 1j*sol.x[1]
    omega_star = omega_branch(Ufun, alpha_star, N, ymin, ymax, omega_ref)
    fnorm = float(np.linalg.norm(sol.fun))
    return alpha_star, omega_star, sol.success, fnorm, sol.message


def run_case(label: str, A: float, a: float, b: float, out: Path):
    Ufun = U_profile_factory(A, a, b)

    # multi-start
    seeds = [
        2.2 - 1.75j,  # paper-ish
        2.2 - 1.00j,
        2.0 - 1.75j,
        2.4 - 1.75j,
        2.2 - 0.50j,
        1.8 - 1.75j,
    ]

    best = None
    for s in seeds:
        alpha_star, omega_star, success, fnorm, msg = pinch(Ufun, N=220, ymin=-6, ymax=6, h=2e-3, alpha_init=s)
        r = Result(label, A, a, b, alpha_star, omega_star, success, fnorm, str(msg))
        if best is None or r.omega_star.imag > best.omega_star.imag:
            best = r

    report = {
        "label": best.label,
        "A": best.A,
        "a": best.a,
        "b": best.b,
        "alpha_star": [best.alpha_star.real, best.alpha_star.imag],
        "omega_star": [best.omega_star.real, best.omega_star.imag],
        "Im_omega": best.omega_star.imag,
        "classification": "absolute" if best.omega_star.imag > 0 else "convective",
        "root_success": bool(best.success),
        "fnorm": best.fnorm,
        "message": best.message,
    }

    out.write_text(json.dumps(report, indent=2))
    return best, report


def main():
    outdir = Path("/users/zwang197/.openclaw/workspace/triantafyllou_re140k_verify")
    outdir.mkdir(parents=True, exist_ok=True)

    # Table 3 (from the PDF page 475):
    # x/d=1.0: A=0.75, a=4.0, b=0.08
    # x/d=2.0: A=0.60, a=3.2, b=0.07
    cases = [
        ("Re140k_xd1", 0.75, 4.0, 0.08),
        ("Re140k_xd2", 0.60, 3.2, 0.07),
    ]

    for label, A, a, b in cases:
        best, report = run_case(label, A, a, b, outdir / f"{label}.json")
        print(f"\n== {label} ==")
        print(f"U(y)=1-A + A*tanh(a*(y^2-b)); A={A}, a={a}, b={b}")
        print(f"alpha* = {best.alpha_star}")
        print(f"omega* = {best.omega_star}")
        print(f"Im(omega*) = {best.omega_star.imag:.6e} -> {report['classification']}")
        print(f"root: success={best.success}, fnorm={best.fnorm:.2e}")


if __name__ == "__main__":
    main()
