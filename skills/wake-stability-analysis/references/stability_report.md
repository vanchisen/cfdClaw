% Spatio-temporal Rayleigh Stability Analysis Toolkit
% Wisp (OpenClaw)
% 2026-02-18

# 1. Summary

This report documents the code generated to perform linear stability analysis of a
parallel wake profile using the **inviscid Orr–Sommerfeld (Rayleigh) equation**, and
its extension to **spatio-temporal Briggs–Bers pinch-point analysis** (complex
wavenumber \(\alpha\) and complex frequency \(\omega\)).

Two validations / applications are included:

1. **Verification against Triantafyllou et al. (JFM 1986) at \(Re=140{,}000\)** using
   the paper’s fitted wake profile parameters (Table 3) and the Rayleigh/Briggs–Bers
   methodology.
2. **Search for the most unstable wake profile** from the dataset
   `Re11K_DNS.dat` by scanning streamwise locations \(x\in[0.55,1.5]\) and computing
   the pinch-point absolute growth rate \(\Im(\omega^*)\) for each extracted
   cross-wake velocity profile \(U(y)\).

# 2. Code inventory

All code was written to:

- `/users/zwang197/.openclaw/workspace/`

## 2.1 Rayleigh eigenvalue solver

**File:** `rayleigh_chebyshev.py`

Purpose:

- Solve the **temporal** Rayleigh eigenvalue problem for a given base flow \(U(y)\)
  and a (possibly complex) streamwise wavenumber \(\alpha\).
- Returns eigenvalues \(c\) and \(\omega=\alpha c\).

Method:

- **Chebyshev collocation** on $y\in[y_{\min},y_{\max}]$
- Dirichlet boundary conditions: $\phi(y_{\min})=\phi(y_{\max})=0$
- Boundary conditions are enforced by **eliminating boundary unknowns** (interior
  restriction), which avoids spurious infinite eigenvalues in the generalized EVP.

## 2.2 Temporal scan driver for `Re11K_DNS.dat`

**File:** `wake_rayleigh_analysis.py`

Purpose:

- Extract a wake profile \(U(y)\) at specified \(x=x_0\) from a Tecplot-like `.dat`
  file.
- Perform a **temporal** scan over real \(\alpha\) and report the most unstable
  temporal mode (largest \(\Im(\omega)\)).

This provides a “convective-amplifier style” temporal growth scan, but **does not
by itself classify absolute vs convective** instability.

## 2.3 Briggs–Bers pinch-point search for one profile

**File:** `briggs_bers_pinch.py`

Purpose:

- Extract \(U(y)\) at \(x=x_0\) from a `.dat` file.
- Compute the spatio-temporal **pinch point** \((\alpha^*,\omega^*)\) satisfying:

$$
D(\alpha,\omega)=0,\qquad \frac{d\omega}{d\alpha}(\alpha^*)=0.
$$

Classification:

- \(\Im(\omega^*)>0\)  → **absolute instability**
- \(\Im(\omega^*)<0\)  → **convective instability**

Numerics:

- \(\omega(\alpha)\) is computed from Rayleigh eigenvalues \(\omega=\alpha c\)
- A single analytic branch is selected using a **nearest-eigenvalue continuation
  heuristic** relative to a reference \(\omega\).
- \(d\omega/d\alpha\) is approximated with a **centered finite difference** along
  the real direction:

$$
\frac{d\omega}{d\alpha}\approx\frac{\omega(\alpha+h)-\omega(\alpha-h)}{2h}.
$$

- Solve \(\Re(d\omega/d\alpha)=0\) and \(\Im(d\omega/d\alpha)=0\) for
  \((\alpha_r,\alpha_i)\) using `scipy.optimize.root`.

## 2.4 Scan pinch-point over \(x\) to locate the most unstable profile

**File:** `scan_pinch_over_x.py`

Purpose:

- Scan \(x\) in a specified interval.
- For each \(x\), extract \(U(y)\) and compute \((\alpha^*,\omega^*)\) via a
  pinch-point search.
- Record \(\Im(\omega^*)\) vs \(x\) and report the maximum.

Robustness:

- Uses **multi-start** initial guesses for \(\alpha\) and picks the result with
  largest \(\Im(\omega^*)\) among acceptable solutions.

# 3. Governing equations

## 3.1 Rayleigh equation

For a parallel base flow \(U(y)\), normal modes of the form
\(\phi(y)\,e^{i(\alpha x-\omega t)}\) satisfy the inviscid Orr–Sommerfeld
(**Rayleigh**) equation:

$$
(U-c)(\phi''-\alpha^2\phi)-U''\phi=0,
\qquad c=\frac{\omega}{\alpha}.
$$

This can be rearranged into a generalized eigenvalue problem for \(c\):

$$
\bigl(U\,L-U''\bigr)\phi = c\,L\phi,
\qquad L=\frac{d^2}{dy^2}-\alpha^2.
$$

## 3.2 Briggs–Bers pinch point

The spatio-temporal dispersion relation \(D(\alpha,\omega)=0\) is implicit in the
Rayleigh eigenproblem. A Briggs–Bers pinch (saddle) point satisfies

$$
D(\alpha^*,\omega^*)=0,\qquad \left.\frac{d\omega}{d\alpha}\right|_{\alpha^*}=0.
$$

The sign of \(\Im(\omega^*)\) determines absolute vs convective behavior.

# 4. Verification against Triantafyllou et al. (1986), \(Re=140{,}000\)

## 4.1 Profile used (paper’s fit)

Triantafyllou et al. fit measured wake profiles (Cantwell 1976) using (eq. 14 in the
paper, with \(d=1\) and \(U_0=1\)):

$$
U(y)=1-A + A\tanh\bigl(a(y^2-b)\bigr).
$$

Table 3 (page 475 of the PDF) gives parameters:

| Case | \(x/d\) | \(A\) | \(a\) | \(b\) |
|---:|---:|---:|---:|---:|
| 1 | 1.0 | 0.75 | 4.0 | 0.08 |
| 2 | 2.0 | 0.60 | 3.2 | 0.07 |

## 4.2 Verification script

**File:** `verify_triantafyllou_re140k.py`

This script runs a pinch-point search on both fitted profiles and writes JSON
reports to:

- `/users/zwang197/.openclaw/workspace/triantafyllou_re140k_verify/`

## 4.3 Results

### (a) \(x/d=1\): absolute instability

Computed:

- \(\alpha^* = 2.1683935915 - 1.8224611370\,i\)
- \(\omega^* = 1.3370198653 + 0.0865043763\,i\)
- \(\Im(\omega^*) = 0.08650>0\) → **absolute**

Paper reports (from the text):

- \(\omega_R\approx 1.3\)
- \(\omega_I\approx 0.087\)

Agreement is good, in particular for \(\omega_I\).

### (b) \(x/d=2\): convective instability

Computed:

- \(\omega^* = 1.2962251462 - 0.4949791758\,i\)
- \(\Im(\omega^*)<0\) → **convective**

This matches the paper’s statement that at \(x/d=2\) the instability is convective.

# 5. Application to `Re11K_DNS.dat`: finding the most unstable profile

## 5.1 Data source and slicing

**Data file:**

- `/users/zwang197/Works/NeuroSEM/Reduced_Model/Re11K/phaseAve/X0-55/Post_new/Re11K_DNS.dat`

The file is a Tecplot-like ASCII dataset with columns including \(X\), \(Y\), \(U\),
... (the scripts read the first 11 numeric columns and use \(X\), \(Y\), \(U\)).

To obtain a wake profile at a given \(x_0\), points satisfying
\(|x-x_0|\le\texttt{tol}\) are selected and then grouped by \(y\) (with rounding) to
average duplicates.

## 5.2 Pinch-point scan over \(x\)

We scanned \(x\in[0.55,1.5]\) with step \(0.05\) and computed a pinch point
\((\alpha^*,\omega^*)\) for each profile. The scan results were saved to:

- `/users/zwang197/.openclaw/workspace/re11k_pinch_scan_x055_15/pinch_scan.csv`

The script reports the \(x\) location with maximum \(\Im(\omega^*)\) (“most unstable
profile”) among the scan points.

## 5.3 Outcome (most unstable profile in the scanned range)

The most unstable profile (maximum absolute growth rate) found in the scan was:

- \(x\_\text{mean} \approx 0.89996824\)
- \(\alpha^* = 2.3549742274 - 1.1001251015\,i\)
- \(\omega^* = 1.0825914294 + 0.4910601027\,i\)
- \(\Im(\omega^*) \approx 0.49106\) → **absolute instability**

# 6. Limitations and recommended next checks

1. **Branch tracking:** pinch-point analysis requires consistent tracking of the
   relevant analytic branch \(\omega(\alpha)\). The current implementation uses a
   nearest-eigenvalue heuristic; it is effective when started near the saddle but
   can jump branches for difficult profiles.
2. **Domain truncation:** Rayleigh assumes an unbounded cross-stream domain.
   Truncation $[y_{\min},y_{\max}]$ should be widened when possible.
3. **Parallel-flow assumption:** results are local to each slice and do not include
   non-parallel corrections.
4. **Inviscid model:** viscosity is neglected in the perturbation equations.

# Appendix A. Reproducing the main results

## A.1 Triantafyllou \(Re=140k\) verification

Run:

```bash
cd /users/zwang197/.openclaw/workspace
python verify_triantafyllou_re140k.py
```

## A.2 Pinch scan for `Re11K_DNS.dat`

Run:

```bash
cd /users/zwang197/.openclaw/workspace
python scan_pinch_over_x.py \
  --dat /users/zwang197/Works/NeuroSEM/Reduced_Model/Re11K/phaseAve/X0-55/Post_new/Re11K_DNS.dat \
  --x-min 0.55 --x-max 1.5 --x-step 0.05 \
  --tol 5e-4 --N 160 --h 1e-3 \
  --outdir /users/zwang197/.openclaw/workspace/re11k_pinch_scan_x055_15
```
