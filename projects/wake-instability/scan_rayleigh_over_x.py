#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

import numpy as np

ALPHA_RE = re.compile(r"^\s*alpha\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*$")
OMEGA_RE = re.compile(r"^\s*omega\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)([+-]\d*\.?\d+(?:[eE][+-]?\d+)?)i\s*$")


def parse_best(stdout: str):
    alpha = None
    omega_r = None
    omega_i = None
    in_best = False
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("Most unstable (temporal) among scanned alphas:"):
            in_best = True
            continue
        if not in_best:
            continue
        ma = ALPHA_RE.match(s)
        if ma:
            alpha = float(ma.group(1))
            continue
        mo = OMEGA_RE.match(s)
        if mo:
            omega_r = float(mo.group(1))
            omega_i = float(mo.group(2))
            continue
    if alpha is None or omega_r is None or omega_i is None:
        raise ValueError("Could not parse best alpha/omega from solver output")
    return alpha, omega_r, omega_i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", required=True, type=Path)
    ap.add_argument("--x-min", default=0.6, type=float)
    ap.add_argument("--x-max", default=2.0, type=float)
    ap.add_argument("--x-step", default=0.05, type=float)
    ap.add_argument("--tol", default=1e-4, type=float)
    ap.add_argument("--N", default=220, type=int)
    ap.add_argument("--alpha-min", default=0.1, type=float)
    ap.add_argument("--alpha-max", default=6.0, type=float)
    ap.add_argument("--alpha-n", default=100, type=int)
    ap.add_argument("--outdir", default=Path("rayleigh_scan_x"), type=Path)
    args = ap.parse_args()

    workdir = Path(__file__).resolve().parent
    args.outdir.mkdir(parents=True, exist_ok=True)

    xs = np.round(np.arange(args.x_min, args.x_max + 1e-12, args.x_step), 10)
    results = []

    for x in xs:
        xstr = f"{x:.2f}"
        subdir = args.outdir / f"x_{xstr}"
        subdir.mkdir(parents=True, exist_ok=True)
        cmd = [
            "python3", "wake_rayleigh_analysis.py",
            "--dat", str(args.dat),
            "--x0", xstr,
            "--tol", str(args.tol),
            "--N", str(args.N),
            "--alpha-min", str(args.alpha_min),
            "--alpha-max", str(args.alpha_max),
            "--alpha-n", str(args.alpha_n),
            "--outdir", str(subdir),
        ]
        p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        out = p.stdout + ("\n" + p.stderr if p.stderr else "")
        (subdir / "stdout.txt").write_text(out)

        if p.returncode != 0:
            results.append((x, None, None, None, "FAILED"))
            print(f"x={xstr}: FAILED")
            continue

        try:
            alpha, omega_r, omega_i = parse_best(p.stdout)
            results.append((x, alpha, omega_r, omega_i, "OK"))
            print(f"x={xstr}: alpha={alpha:.6f}, omega={omega_r:+.6e}{omega_i:+.6e}i")
        except Exception as e:
            results.append((x, None, None, None, "PARSE_FAIL"))
            print(f"x={xstr}: PARSE_FAIL ({e})")

    summary_csv = args.outdir / "rayleigh_scan_summary.csv"
    with summary_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x", "alpha", "omega_real", "omega_imag", "status"])
        for row in results:
            w.writerow(row)

    ok = [r for r in results if r[4] == "OK"]
    if ok:
        best = max(ok, key=lambda r: r[3])
        print("\nGlobal most unstable x in scanned range:")
        print(f"  x     = {best[0]:.6f}")
        print(f"  alpha = {best[1]:.6f}")
        print(f"  omega = {best[2]:+.6e}{best[3]:+.6e}i")
    else:
        print("\nNo successful runs.")

    print(f"Wrote summary: {summary_csv}")


if __name__ == "__main__":
    main()
