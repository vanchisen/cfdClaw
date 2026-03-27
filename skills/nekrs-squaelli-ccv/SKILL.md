---
name: nekrs-squaelli-ccv
description: Set up and stabilize nekRS SquaElli cases on CCV. Use for generating cyl.msh/cyl.re2, setting periodic BCs in gmsh2nek, syncing cases to CCV, and applying stable timestep/regularization settings.
---

# nekRS SquaElli (CCV)

## When to use
- Preparing new SquaElli cases (I/Y series)
- Regenerating meshes / `cyl.re2`
- Syncing cases to CCV and submitting jobs
- Stabilizing runs via `cyl.par` adjustments

## Stable run parameters (key takeaways)
For stability (empirically validated in Y20):
```
dt = targetCFL=1.2 + max=2e-3 + initial = 1e-3
regularization = hpfrt + nModes=1 + scalingCoeff=10
```
Apply these to `cyl.par` for cases that blow up, then resubmit.

## Mesh generation workflow
### 1) Geometry
- `cyl.geo` uses `YC0` for ellipse center (e.g., Y01 → `YC0=0.01`).

### 2) Mesh (Gmsh)
Use the local Gmsh build:
```
~/Documents/Apps/gmsh-4.*/bin/gmsh
```
Run the `.geo` directly so the script controls export options:
```
gmsh cyl.geo -0
```
Ensure the following are set inside `cyl.geo`:
- `SetOrder 2;`
- `Mesh.MshFileVersion = 2.2;`
- `Mesh.SaveAll = 0;`
- `Save "cyl.msh";` (uncommented)

### 3) `gmsh2nek` → `cyl.re2`
Binary:
```
/users/zwang197/Works/NeuroSEM/Toyota/Mesh/gmsh2nek
```
**Non‑periodic (no periodic pairs):**
```
3
cyl
0
0
cyl
```

**Periodic (two pairs, 4–5 and 6–7):**
```
3
cyl
0
2
4 5
6 7
cyl
```
This produces `cyl.re2` directly (no rename needed).

## CCV sync + run pattern
CCV destination:
```
/users/zwang197/scratch/zwang/nekRS/SquaElli/IXX
/users/zwang197/scratch/zwang/nekRS/SquaElli/YXX
```
Files to sync:
- `cyl.geo`, `cyl.msh`, `cyl.re2`
- `cyl.par`, `cyl.udf`, `cyl.oudf`, `cyl.usr`
- `runme.nekRs`

Submit on CCV:
```
cd /users/zwang197/scratch/zwang/nekRS/SquaElli/<case>
sbatch runme.nekRs
```

## References
- `references/nekrs_stability_notes.md`
