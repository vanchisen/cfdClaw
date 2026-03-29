% Instability Analysis Report
% Wisp (OpenClaw)
% 2026-03-27

# Summary

This report documents the **Triantafyllou-style wake stability analysis** performed using the inviscid Rayleigh equation and Briggs–Bers pinch-point criterion. It covers:

1. **Validation** against Triantafyllou et al. (1986) at Re = 140k.
2. **Re11K_DNS** scan (x in [0.6, 2.0]) with sanity filtering.
3. **Re40K (A5I40_Re40K.dat)** scan (x in [0.9, 3.0]) on both raw and interpolated x grids.

# Method Overview

We solve the inviscid Orr–Sommerfeld (Rayleigh) equation for a parallel wake profile U(y):

$$
(U-c)(\phi''-\alpha^2\phi) - U''\phi = 0,\qquad c=\frac{\omega}{\alpha}.
$$

A Briggs–Bers pinch point satisfies

$$
D(\alpha,\omega)=0,\qquad \frac{d\omega}{d\alpha}=0.
$$

Classification:
- **Absolute** if Im(omega*) > 0
- **Convective** if Im(omega*) < 0

The numerical workflow uses:
- Chebyshev collocation Rayleigh solver
- Multi-start pinch-point root search
- Optional sanity filter: **|Im(omega*)| < 1** and **success=True**

# 1. Triantafyllou Re=140k Validation

Output files:
- `/users/zwang197/.openclaw/workspace/triantafyllou_re140k_verify/Re140k_xd1.json`
- `/users/zwang197/.openclaw/workspace/triantafyllou_re140k_verify/Re140k_xd2.json`

**Results (reproduced):**

| Case | alpha* | omega* | Im(omega*) | Classification |
|---|---|---|---:|---|
| x/d = 1 | 2.1683935914 - 1.8224611372 i | 1.3370198653 + 0.0865043763 i | +0.0865044 | Absolute |
| x/d = 2 | 0.9747575953 - 2.3836716884 i | 1.2962251462 - 0.4949791758 i | -0.4949792 | Convective |

These match Triantafyllou et al. (1986): omega_R ~ 1.3 and omega_I ~ 0.087 at x/d=1, and convective behavior at x/d=2.

# 2. Re11K_DNS Scan (x in [0.6, 2.0])

Data:
- `/users/zwang197/Works/NeuroSEM/Reduced_Model/Re11K/phaseAve/X0-55/Post_new/Re11K_DNS.dat`

Scan output:
- `/users/zwang197/.openclaw/workspace/re11k_pinch_scan_x060_20_rerun/pinch_scan.csv`
- filtered: `/users/zwang197/.openclaw/workspace/re11k_pinch_scan_x060_20_rerun/pinch_scan_filtered_ImLt1.csv`

**Most unstable (after filter |Im|<1 and success=True):**

- **x ~ 0.899968**
- alpha* = 2.3549742274 - 1.1001251015 i
- omega* = 1.0825914294 + 0.4910601027 i
- Im(omega*) = **0.4910601** (absolute)

U(y) profile saved at:
- `/users/zwang197/.openclaw/workspace/re11k_pinch_scan_x060_20_rerun/most_unstable_profile_x0.899968.csv`

# 3. Re40K Toyota (A5I40_Re40K.dat)

Data:
- `/users/zwang197/Works/NeuroSEM/Toyota/runs/Re40K_Dats/A5I40_Re40K.dat`

**Important:** This Tecplot file has columns:
`X, Y, Z, U, V, W, P, T, S01, S02`, so **U is column 4** (index 3).

## 3.1 Direct scan at available x values (x in [0.9, 3.0])

Scan output:
- `/users/zwang197/.openclaw/workspace/re40k_pinch_scan_x090_30/pinch_scan.csv`
- filtered: `/users/zwang197/.openclaw/workspace/re40k_pinch_scan_x090_30/pinch_scan_filtered_ImLt1.csv`

**Most unstable (filtered):**

- **x = 1.000000**
- alpha* = 2.5262355843 - 1.6673414799 i
- omega* = 1.9893156786 + 0.3830957350 i
- Im(omega*) = **0.3830957** (absolute)

U(y) profile saved at:
- `/users/zwang197/.openclaw/workspace/re40k_pinch_scan_x090_30/most_unstable_profile_x1.000000.csv`

## 3.2 Interpolated scan (10 uniform x points in [0.9, 3.0])

Interpolated scan output:
- `/users/zwang197/.openclaw/workspace/re40k_pinch_scan_x090_30_interp10/pinch_scan_interp10.csv`

**Most unstable (interpolated grid):**

- **x = 2.300000**
- alpha* = 0.3256190959 + 4.6947183377 i
- omega* = 0.0489206381 + 0.2665531145 i
- Im(omega*) = **0.2665531** (absolute)

U(y) profile saved at:
- `/users/zwang197/.openclaw/workspace/re40k_pinch_scan_x090_30_interp10/most_unstable_profile_x2.300000.csv`

# 4. Re5K DNS (z-line-averaged slice, interpolated onto regular x-y grid)

Data source:
- `/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/Re5K_DNS.dat`

Because the original Tecplot slice is irregular in `(x,y)`, the wake profiles were first interpolated onto a regular grid over:
- `x in [0.6, 3.0]`
- `y in [-5, 5]`

Interpolated field:
- `/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/Re5K_DNS_xy_regular.dat`

## 4.1 Coarse scan on regular grid

Coarse scan output:
- `/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/re5k_pinch_scan_xy_regular_x060_30_coarse/pinch_scan.csv`

Raw coarse maximum:
- `x = 2.7`
- `Im(omega*) = 3.4417360`

However, the downstream high-growth branches (`x=2.4, 2.7, 3.0`) are likely **spurious branch picks** because they show strongly nonphysical-looking complex wavenumbers and unrealistically large growth rates.

Most credible coarse unstable region:
- **`x ~ 1.2`**
- `alpha* = 1.9165670030 - 1.3369685900 i`
- `omega* = 1.42740897 + 0.50022246 i`
- `Im(omega*) = 0.50022246` (absolute)

## 4.2 Refined scan on regular grid (`x in [1.0, 1.4]`)

Refined scan output:
- `/users/zwang197/Works/NeuroSEM/Re5K_DNS_CCV/re5k_pinch_scan_xy_regular_x100_14_refined/pinch_scan.csv`

Raw refined maximum:
- `x = 1.15`
- `alpha* = 1.0666625191 - 5.6554256266 i`
- `omega* = 0.3930684435 + 2.0112375872 i`
- `Im(omega*) = 2.0112375872`

Again, the largest-growth refined cases (`x=1.10, 1.15, 1.20`) appear to be branch-jump artifacts because they have very large negative `Im(alpha*)` and disproportionately large growth rates relative to neighboring points.

Most credible refined unstable location (sanity-filtered interpretation):
- **`x ~ 1.4`**
- `alpha* = 1.8727072381 - 0.9608027740 i`
- `omega* = 1.29091764 + 0.42830964 i`
- `Im(omega*) = 0.42831` (absolute)

A nearby physically plausible band is:
- `x = 1.30` → `Im(omega*) = 0.38188`
- `x = 1.35` → `Im(omega*) = 0.41484`
- `x = 1.40` → `Im(omega*) = 0.42831`

So the present best estimate of the **most unstable physical wake location** for this Re5K regularized dataset is:
- **`x ≈ 1.4`**

# Notes / Caveats

- Pinch-point searches can jump branches; the **|Im(omega*)| < 1** filter helps reject spurious solutions.
- A **spurious branch** means the solver converged to a mathematically valid but physically irrelevant eigenvalue branch rather than the wake mode of interest. Typical warning signs are abrupt jumps in `Im(omega*)`, discontinuous changes in `alpha*`, and isolated very large growth rates that do not continue smoothly with neighboring x locations.
- Interpolated-x results depend on the interpolation between available x slices.
- The Re40K dataset has sparse x locations; interpolation is recommended if uniform sampling is required.
- For Re5K regular-grid scans, additional sanity checks on `alpha*` are needed; raw maxima can be dominated by nonphysical branch selections. In the refined Re5K scan, the large-growth cases near `x=1.10-1.20` were therefore treated as likely spurious, and the smoother branch near `x=1.30-1.40` was taken as the more credible physical instability band.

# Files / Scripts

Key scripts used:
- `rayleigh_chebyshev.py`
- `briggs_bers_pinch.py`
- `scan_pinch_over_x.py`
- `verify_triantafyllou_re140k.py`

Skill bundle:
- `cfdClaw/skills/wake-stability-analysis/`
