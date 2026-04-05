#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from rayleigh_chebyshev import rayleigh_temporal

OUTDIR = Path(__file__).resolve().parent / 'triantafyllou_fig4_7_outputs'
OUTDIR.mkdir(exist_ok=True)


def rectilinear_wake_profile(U0_over_Uinf: float, h0_over_H0: float, H0: float = 1.0):
    """Piecewise-constant simple wake model from paper fig. 3, smoothed slightly.

    We model:
      U = U0            for |y| <= h0
      U = Uinf          for h0 < |y| <= H0
      U = Uinf          outside

    Since the Rayleigh Chebyshev solver needs a differentiable profile, replace the
    jump by narrow tanh transitions. This is an approximation to the paper's exact
    rectilinear model, but it preserves the key control parameters.
    """
    Uinf = 1.0
    U0 = U0_over_Uinf * Uinf
    h0 = h0_over_H0 * H0
    delta = 0.02 * H0

    def U(y):
        y = np.asarray(y, dtype=float)
        s = np.abs(y)
        # core wake deficit inside |y|<h0, transition to outer uniform flow
        return Uinf - (Uinf - U0) * 0.5 * (1.0 - np.tanh((s - h0) / delta))

    return U


def map_ki_lines(Ufun, kis, kr_min=0.05, kr_max=2.5, nkr=80, N=120, ymin=-4.0, ymax=4.0):
    curves = []
    for ki in kis:
        pts = []
        for kr in np.linspace(kr_min, kr_max, nkr):
            alpha = kr + 1j * ki
            try:
                _, c, omega = rayleigh_temporal(Ufun, alpha, N=N, ymin=ymin, ymax=ymax)
                if len(omega) == 0:
                    continue
                w = omega[0]
                if np.isfinite(w.real) and np.isfinite(w.imag):
                    pts.append((kr, w.real, w.imag))
            except Exception:
                continue
        curves.append((ki, np.array(pts, dtype=float) if pts else np.empty((0, 3))))
    return curves


def plot_case(fig_no, U0_over_Uinf, h0_over_H0, kis):
    Ufun = rectilinear_wake_profile(U0_over_Uinf, h0_over_H0)
    curves = map_ki_lines(Ufun, kis)

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for i, (ki, pts) in enumerate(curves, start=1):
        if len(pts) == 0:
            continue
        ax.plot(pts[:, 1], pts[:, 2], '-', lw=1.4, label=f'k_i={ki:.2f}')
        # label near end of curve
        j = min(len(pts)-1, max(0, int(0.75*len(pts))))
        ax.text(pts[j,1], pts[j,2], str(i), fontsize=8)

    ax.axhline(0.0, color='k', lw=0.8, alpha=0.5)
    ax.set_xlabel(r'$\omega_r$')
    ax.set_ylabel(r'$\omega_i$')
    ax.set_title(f'Approximate reproduction of paper Fig. {fig_no}\nU0/Uinf={U0_over_Uinf}, h0/H0={h0_over_H0}')
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    png = OUTDIR / f'fig_{fig_no}_approx.png'
    csv = OUTDIR / f'fig_{fig_no}_curves.csv'
    fig.savefig(png, dpi=180)
    plt.close(fig)

    with csv.open('w') as f:
        f.write('curve_index,ki,kr,omega_r,omega_i\n')
        for i, (ki, pts) in enumerate(curves, start=1):
            for row in pts:
                f.write(f'{i},{ki},{row[0]},{row[1]},{row[2]}\n')

    return png, csv


def main():
    cases = [
        (4, 0.0, 0.3,  [0.0, -0.2, -0.4, -0.6, -0.8]),
        (5, 0.0, 0.5,  [0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2]),
        (6, 0.1, 0.3,  [0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2, -1.4]),
        (7, 0.0, 0.95, [0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2]),
    ]
    summary = []
    for fig_no, u0, h0, kis in cases:
        png, csv = plot_case(fig_no, u0, h0, kis)
        summary.append((fig_no, str(png), str(csv)))
        print(f'Generated Fig. {fig_no}: {png}')

    sm = OUTDIR / 'summary.md'
    with sm.open('w') as f:
        f.write('# Triantafyllou 1986 figure 4-7 approximate reproductions\n\n')
        f.write('These are approximate reproductions using the existing Rayleigh-Chebyshev solver and a smoothed rectilinear wake profile.\n')
        f.write('They are useful for qualitative validation, but not yet exact reproductions of the paper\'s analytical piecewise-rectilinear model.\n\n')
        for fig_no, png, csv in summary:
            f.write(f'- Fig. {fig_no}: `{png}` and `{csv}`\n')
    print(f'Wrote summary: {sm}')


if __name__ == '__main__':
    main()
