#!/usr/bin/env python3
from __future__ import annotations

import cmath
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

OUTDIR = Path(__file__).resolve().parent / 'triantafyllou_fig4_7_exact_outputs'
OUTDIR.mkdir(exist_ok=True)


def dispersion_roots(k: complex, u0: float, h: float):
    """Quadratic dispersion relation from the scanned paper page.

    Equations read from page 465:
      Δ(ω,k) = A ω^2 + B ω + C = 0
      A = 2[1 + tanh(kh)]
      B = -2{[1+tanh(kh)] k u0 + Δ0} - [1+tanh(kh)] (2k-Δ0)
          + Δ0 exp[-2k(1-h)] [1-tanh(kh)]
      C = (2k-Δ0){[1+tanh(kh)] k u0 + Δ0}
          - Δ0 exp[-2k(1-h)] {[1-tanh(kh)] k u0 - Δ0}

    with
      Δ0 = (U0-UA) H0 / (δ U0) = (1-u0)/(1-h)
    because δ = H0-h0 = (1-h)H0 and u0 = UA/U0.
    """
    d = 1.0 - h
    Delta0 = (1.0 - u0) / d
    th = cmath.tanh(k * h)
    em = cmath.exp(-2.0 * k * d)

    A = 2.0 * (1.0 + th)
    B = -2.0 * (((1.0 + th) * k * u0) + Delta0) - (1.0 + th) * (2.0 * k - Delta0) + Delta0 * em * (1.0 - th)
    C = (2.0 * k - Delta0) * (((1.0 + th) * k * u0) + Delta0) - Delta0 * em * (((1.0 - th) * k * u0) - Delta0)

    disc = B * B - 4.0 * A * C
    sdisc = cmath.sqrt(disc)
    w1 = (-B + sdisc) / (2.0 * A)
    w2 = (-B - sdisc) / (2.0 * A)
    return w1, w2


def trace_branch(u0: float, h: float, ki: float, kr_values: np.ndarray, branch: int):
    roots0 = dispersion_roots(complex(kr_values[0], ki), u0, h)
    w_prev = roots0[branch]
    out = [(kr_values[0], w_prev.real, w_prev.imag)]

    for kr in kr_values[1:]:
        roots = dispersion_roots(complex(kr, ki), u0, h)
        if abs(roots[0] - w_prev) <= abs(roots[1] - w_prev):
            w = roots[0]
        else:
            w = roots[1]
        out.append((kr, w.real, w.imag))
        w_prev = w
    return np.array(out, dtype=float)


def plot_case(fig_no: int, u0: float, h: float, kis: list[float], kr_min=0.02, kr_max=2.2, nkr=500):
    kr_values = np.linspace(kr_min, kr_max, nkr)
    # paper figures appear to follow one continuous analytic branch; pick branch per figure
    branch_map = {4: 0, 5: 0, 6: 0, 7: 0}
    branch = branch_map.get(fig_no, 0)
    curves = []
    for ki in kis:
        pts = trace_branch(u0, h, ki, kr_values, branch=branch)
        curves.append((ki, pts))

    axis_limits = {
        4: ((0.25, 1.25), (-0.75, 0.50)),
        5: ((0.25, 1.25), (-0.75, 0.25)),
        6: ((0.25, 1.25), (-0.75, 0.25)),
        7: ((0.25, 1.25), (-0.75, 0.50)),
    }

    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    for i, (ki, pts) in enumerate(curves, start=1):
        ax.plot(pts[:,1], pts[:,2], '-', lw=1.6)
        j = min(len(pts)-1, max(0, int(0.15*len(pts))))
        ax.text(pts[j,1], pts[j,2], str(i), fontsize=9)

    ax.axhline(0.0, color='k', lw=0.9, alpha=0.5)
    ax.set_xlabel(r'$\omega_R$')
    ax.set_ylabel(r'$\omega_I$')
    ax.set_title(f'Triantafyllou 1986 exact-model reproduction: Fig. {fig_no}\n$u_0$={u0}, $h$={h}')
    if fig_no in axis_limits:
        (xmin, xmax), (ymin, ymax) = axis_limits[fig_no]
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    png = OUTDIR / f'fig_{fig_no}_exact.png'
    csv = OUTDIR / f'fig_{fig_no}_exact.csv'
    fig.savefig(png, dpi=220)
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
    lines = ['# Exact-model reproductions for Triantafyllou 1986 figs 4-7\n']
    for fig_no, u0, h, kis in cases:
        png, csv = plot_case(fig_no, u0, h, kis)
        print(f'Generated Fig. {fig_no}: {png}')
        lines.append(f'- Fig. {fig_no}: `{png}` and `{csv}`\n')
    (OUTDIR / 'summary.md').write_text(''.join(lines))
    print(f'Wrote summary: {OUTDIR / "summary.md"}')


if __name__ == '__main__':
    main()
