#!/usr/bin/env python3
"""triantafyllou_validation.py

Reproduce results from Triantafyllou, Triantafyllou & Chryssostomidis (1986)
J. Fluid Mech. 170, 461-477.

Profile (eq. 14):
    U(y) / U_inf = 1 - A * sech^2(a * |y/d|^b)

where y is in units of cylinder diameter d, U_inf is the free-stream speed.

Validation targets (Table 2, Re = 56, symmetric mode):
    x/d = 2.0 : omega_R = 0.82, omega_I = 0.037, k_R = 1.1,  k_I = -1.15  -> ABS
    x/d = 3.5 : omega_R = 0.83, omega_I = 0,     k_R = 1.45, k_I = -0.75  -> marginal
    x/d = 5.0 : omega_R = 0.83, omega_I = 0,     k_R = 1.2,  k_I = -0.30  -> conv
    x/d = 8.0 : omega_R = 0.83, omega_I = 0,     k_R = 1.05, k_I = -0.08  -> conv
    x/d = 20.0: omega_R = 0.83, omega_I = 0,     k_R = 0.90, k_I = -0.01  -> conv

Strouhal number St = omega_R / (2*pi) ~ 0.13 for the absolute mode.
"""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rayleigh_chebyshev import rayleigh_temporal, rayleigh_absolute, _track_omega

# ---------------------------------------------------------------------------
# Profile parameters from Table 1 (Re = 56)
# ---------------------------------------------------------------------------
TABLE1_RE56: dict[float, dict] = {
    2.0:  dict(A=0.53, a=2.25, b=0.52),
    3.5:  dict(A=0.56, a=1.60, b=0.50),
    5.0:  dict(A=0.58, a=1.00, b=0.25),
    8.0:  dict(A=0.36, a=0.55, b=0.25),
    20.0: dict(A=0.20, a=0.20, b=0.25),
}

# Table 3: Re = 140000
TABLE3_RE140K: dict[float, dict] = {
    1.0: dict(A=0.75, a=4.0, b=0.08),
    2.0: dict(A=0.60, a=3.2, b=0.07),
}

# Re = 34 (subcritical, single profile at x/d=2)
PARAMS_RE34_XD2 = dict(A=0.54, a=1.7, b=0.50)


def triantafyllou_profile(A: float, a: float, b: float):
    """U(y) = 1 - A * sech^2(a * |y|^b),  y in units of d."""
    def U(y: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=float)
        xi = a * np.abs(y) ** b
        return 1.0 - A / np.cosh(xi) ** 2
    return U


def temporal_scan(Ufun, kR_arr, N=200, ymin=-15.0, ymax=15.0):
    """Scan real wavenumber kR, return array of most-unstable omega."""
    omegas = []
    for kR in kR_arr:
        _, _, omega = rayleigh_temporal(Ufun, kR, N=N, ymin=ymin, ymax=ymax)
        omegas.append(omega[0])
    return np.array(omegas)


def omega_plane_map(
    Ufun,
    kI_values: list[float],
    kR_arr: np.ndarray,
    N: int = 150,
    ymin: float = -15.0,
    ymax: float = 15.0,
) -> dict[float, np.ndarray]:
    """Map lines kI = const from k-plane to omega-plane.

    For each kI, scan kR and compute the tracked dominant omega(kR + i*kI).
    Uses eigenvector tracking for continuity across complex alpha.
    Returns {kI: array_of_omega}.
    """
    curves: dict[float, np.ndarray] = {}
    for kI in kI_values:
        omegas = []
        omega_ref = None
        evec_ref = None
        for kR in kR_arr:
            k = complex(kR, kI)
            omega_val, evec = _track_omega(
                Ufun, k, N, ymin, ymax, omega_ref=omega_ref, evec_ref=evec_ref
            )
            omegas.append(omega_val)
            omega_ref = omega_val
            evec_ref = evec
        curves[kI] = np.array(omegas)
    return curves


def find_saddle(Ufun, kR_scan, N=200, ymin=-15.0, ymax=15.0) -> tuple:
    """Find the Briggs-Bers saddle: scan real kR for peak Im(omega), then Newton."""
    best_alpha, best_omega_im = kR_scan[len(kR_scan) // 2], -np.inf
    for kr in kR_scan:
        _, _, omega = rayleigh_temporal(Ufun, kr, N=N, ymin=ymin, ymax=ymax)
        if omega[0].imag > best_omega_im:
            best_omega_im = omega[0].imag
            best_alpha = kr
    alpha_s, omega_s, conv, nit = rayleigh_absolute(
        Ufun, complex(best_alpha), N=N, ymin=ymin, ymax=ymax, max_iter=80, tol=1e-8
    )
    return alpha_s, omega_s, conv, nit


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------
def main():
    N = 200
    ymin, ymax = -15.0, 15.0
    kR_scan = np.linspace(0.1, 3.0, 80)

    # ---- Re = 56 : Briggs-Bers table ----------------------------------------
    print("=" * 72)
    print("Triantafyllou et al. (1986) — Re = 56  (cf. Table 2)")
    print("=" * 72)
    print(f"{'x/d':>5}  {'k_s (paper)':>18}  {'omega_s (paper)':>20}  "
          f"{'St':>6}  {'type':>5}")
    paper_table2 = {
        2.0:  (complex(1.1,  -1.15), complex(0.82, +0.037), "ABS"),
        3.5:  (complex(1.45, -0.75), complex(0.83,  0.000), "marg"),
        5.0:  (complex(1.2,  -0.30), complex(0.83,  0.000), "conv"),
        8.0:  (complex(1.05, -0.08), complex(0.83,  0.000), "conv"),
        20.0: (complex(0.90, -0.01), complex(0.83,  0.000), "conv"),
    }
    for xd, (k_paper, om_paper, ptype) in paper_table2.items():
        print(f"  {xd:>4.1f}  k={k_paper.real:+.2f}{k_paper.imag:+.2f}j  "
              f"omega={om_paper.real:+.3f}{om_paper.imag:+.3f}j  "
              f"St={om_paper.real/(2*np.pi):.3f}  [{ptype}]")
    print()

    print(f"{'x/d':>5}  {'k_s (solver)':>26}  {'omega_s (solver)':>26}  "
          f"{'St':>6}  {'type':>5}  {'conv':>5}")
    print("-" * 80)
    for xd, params in TABLE1_RE56.items():
        Ufun = triantafyllou_profile(**params)
        alpha_s, omega_s, conv, nit = find_saddle(Ufun, kR_scan, N=N, ymin=ymin, ymax=ymax)
        St = omega_s.real / (2 * np.pi)
        ptype = "ABS" if omega_s.imag > 0 else "conv"
        print(f"  {xd:>4.1f}  k_s={alpha_s.real:+.4f}{alpha_s.imag:+.4f}j  "
              f"omega_s={omega_s.real:+.4f}{omega_s.imag:+.4f}j  "
              f"St={St:.3f}  [{ptype}]  {str(conv):>5} ({nit}it)")

    # ---- Re = 34 subcritical -------------------------------------------------
    print()
    print("Re = 34 (subcritical) — x/d = 2.0 (should be convective):")
    Ufun34 = triantafyllou_profile(**PARAMS_RE34_XD2)
    alpha_s, omega_s, conv, nit = find_saddle(Ufun34, kR_scan, N=N, ymin=ymin, ymax=ymax)
    St = omega_s.real / (2 * np.pi)
    ptype = "ABS" if omega_s.imag > 0 else "conv"
    print(f"  k_s={alpha_s.real:+.4f}{alpha_s.imag:+.4f}j  "
          f"omega_s={omega_s.real:+.4f}{omega_s.imag:+.4f}j  "
          f"St={St:.3f}  [{ptype}]  conv={conv} ({nit}it)")

    # ---- Re = 140000 ---------------------------------------------------------
    print()
    print("Re = 140000  (cf. Table 3 / Figs 16-17):")
    for xd, params in TABLE3_RE140K.items():
        Ufun = triantafyllou_profile(**params)
        alpha_s, omega_s, conv, nit = find_saddle(Ufun, kR_scan, N=N, ymin=ymin, ymax=ymax)
        St = omega_s.real / (2 * np.pi)
        ptype = "ABS" if omega_s.imag > 0 else "conv"
        print(f"  x/d={xd:.1f}: k_s={alpha_s.real:+.4f}{alpha_s.imag:+.4f}j  "
              f"omega_s={omega_s.real:+.4f}{omega_s.imag:+.4f}j  "
              f"St={St:.3f}  [{ptype}]  conv={conv} ({nit}it)")
    print("  (Paper: x/d=1 absolute with St=0.21; x/d=2 convective)")

    # ---- omega-plane maps: Re=56 x/d=2 (Fig 10) and x/d=3.5 (Fig 11) ------
    print()
    print("Generating omega-plane maps (Figs 10 & 11) ...")

    kI_vals = [0.0, -0.50, -0.75, -1.0, -1.1]
    kR_vals = np.linspace(0.3, 2.2, 100)
    colors = ["C0", "C1", "C2", "C3", "C4"]

    for xd, (ylim_lo, ylim_hi) in [(2.0, (-0.12, 0.42)), (3.5, (-0.12, 0.32))]:
        params = TABLE1_RE56[xd]
        Ufun = triantafyllou_profile(**params)
        curves = omega_plane_map(Ufun, kI_vals, kR_vals, N=150, ymin=ymin, ymax=ymax)

        fig, ax = plt.subplots(figsize=(6.5, 5.5))
        for i, kI in enumerate(kI_vals):
            om = curves[kI]
            ax.plot(om.real, om.imag, color=colors[i],
                    label=f"$k_I = {kI:.2f}$", lw=1.4)
        ax.axhline(0, color="k", lw=0.8, ls="--", alpha=0.6)
        ax.set_xlabel(r"$\omega_R$", fontsize=13)
        ax.set_ylabel(r"$\omega_I$", fontsize=13)
        ax.set_title(
            fr"$\omega$-plane map, $x/d = {xd}$, Re = 56  (cf. Fig. {9 + int(xd)})",
            fontsize=11,
        )
        ax.legend(fontsize=9, loc="upper right")
        ax.set_xlim(0.2, 1.3)
        ax.set_ylim(ylim_lo, ylim_hi)
        fname = f"omega_plane_xd{int(xd*10):02d}_Re56.png"
        plt.tight_layout()
        plt.savefig(fname, dpi=150)
        print(f"  Saved {fname}")
        plt.close()

    print("Done.")


if __name__ == "__main__":
    main()
