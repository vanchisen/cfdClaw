---
name: wake-stability-analysis
description: Perform cylinder-wake stability analysis with Rayleigh + Briggs–Bers pinch-point methods (Triantafyllou 1986). Use for: (1) validating against Triantafyllou Re=140k fitted profiles, (2) scanning x locations in Re11K_DNS.dat to find most unstable wake profile, (3) extracting U(y) at the most unstable x, (4) filtering spurious branches by Im(omega*) sanity checks.
---

# Wake Stability Analysis (Triantafyllou-style)

## Overview
Run inviscid Rayleigh + Briggs–Bers pinch-point analysis on cylinder wake profiles to determine absolute vs convective instability and identify the most unstable wake slice in Re11K DNS data.

## Quick start
1) **Verify against Triantafyllou Re=140k (x/d=1,2)**
```bash
cd /users/zwang197/.openclaw/workspace
python3 skills/wake-stability-analysis/scripts/verify_triantafyllou_re140k.py
```
Outputs JSON to `triantafyllou_re140k_verify/`.

2) **Scan Re11K DNS profiles (pinch point)**
```bash
cd /users/zwang197/.openclaw/workspace
python3 skills/wake-stability-analysis/scripts/scan_pinch_over_x.py \
  --dat /users/zwang197/Works/NeuroSEM/Reduced_Model/Re11K/phaseAve/X0-55/Post_new/Re11K_DNS.dat \
  --x-min 0.6 --x-max 2.0 --x-step 0.05 \
  --tol 5e-4 --N 160 --h 1e-3 \
  --outdir /users/zwang197/.openclaw/workspace/re11k_pinch_scan_x060_20
```
This writes `pinch_scan.csv` and prints the most unstable x (max Im(omega*)).

3) **Apply sanity filter for spurious branches (recommended)**
Keep only solutions with `success=True` and `|Im(omega*)|<1`.

## Workflow (recommended)
1. **Read references**
   - `references/stability_report.md` for method recap and prior results
   - `references/data_paths.md` for the Re11K data path

2. **Triantafyllou verification**
   - Run `scripts/verify_triantafyllou_re140k.py`
   - Confirm:
     - x/d=1 → absolute (Im(omega*) > 0)
     - x/d=2 → convective (Im(omega*) < 0)

3. **Re11K scan**
   - Run `scripts/scan_pinch_over_x.py` over requested x-range
   - Use a sanity filter to reject branch-jump artifacts

4. **Extract most-unstable U(y)**
   - Once the best x is known, extract the U(y) profile and save as CSV
   - Use the same tolerance `tol=5e-4` as the scan

## Outputs
- `triantafyllou_re140k_verify/*.json` (verification reports)
- `re11k_pinch_scan_*/pinch_scan.csv` (full scan)
- `re11k_pinch_scan_*/pinch_scan_filtered_ImLt1.csv` (filtered scan)
- `re11k_pinch_scan_*/most_unstable_profile_x*.csv` (U(y) at best x)

## Scripts
- `scripts/rayleigh_chebyshev.py` — Rayleigh temporal eigenvalue solver
- `scripts/briggs_bers_pinch.py` — pinch-point search for a single profile
- `scripts/scan_pinch_over_x.py` — scan x locations, report Im(omega*)
- `scripts/verify_triantafyllou_re140k.py` — Re=140k verification

## References
- `references/stability_report.md`
- `references/data_paths.md`
