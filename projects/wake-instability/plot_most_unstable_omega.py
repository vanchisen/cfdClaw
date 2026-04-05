#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = Path('/users/zwang197/Works/NeuroSEM/WakeInstability')
RE5K = BASE / 'rayleigh_scan_x_Re5K' / 'rayleigh_scan_summary.csv'
RE11K = BASE / 'rayleigh_scan_x_Re11K' / 'rayleigh_scan_summary.csv'
OUTPNG = BASE / 'most_unstable_alpha_vs_x_Re5K_Re11K.png'
OUTCSV = BASE / 'most_unstable_alpha_vs_x_Re5K_Re11K.csv'


def load_freq(path: Path, label: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df['status'] == 'OK'].copy()
    df['frequency'] = df['omega_real'] / (2.0 * np.pi)
    df['case'] = label
    return df[['x', 'alpha', 'omega_real', 'omega_imag', 'frequency', 'case']]


def main():
    df5 = load_freq(RE5K, 'Re5K')
    df11 = load_freq(RE11K, 'Re11K')
    df = pd.concat([df5, df11], ignore_index=True)
    df.to_csv(OUTCSV, index=False)

    plt.figure(figsize=(8, 5.5))
    plt.plot(df5['x'], df5['alpha'], 'o-', lw=1.8, ms=4, label='Re5K')
    plt.plot(df11['x'], df11['alpha'], 's-', lw=1.8, ms=4, label='Re11K')
    plt.xlabel('x')
    plt.ylabel(r'Most unstable $\alpha$')
    plt.title(r'Most unstable temporal $\alpha$ vs x')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPNG, dpi=200)

    print(f'Wrote plot: {OUTPNG}')
    print(f'Wrote csv:  {OUTCSV}')


if __name__ == '__main__':
    main()
