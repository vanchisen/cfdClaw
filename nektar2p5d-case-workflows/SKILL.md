---
name: nektar2p5d-case-workflows
description: Case-building, geometry editing, CCV run, and Tecplot export workflow for the CFDClaw Nektar2.5D case tree. Use when creating or modifying straight vessels, aneurysm variants, bifurcation-long variants, or when converting checkpoints to .dat with the Brown CCV in-house Nektar2.5D toolchain.
---

# Nektar2.5D Case Workflows

## Use this workflow

- Build geometry with `gmsh -2 -format msh2`
- Convert with `Nektar2.5D/Examples/gmsh2rea.py`
- Run with `Nektar2.5D/SPM_Thermo/Linux/nektarF -chk -z2 -S case.rea`
- Export Tecplot with `Nektar2.5D/Utilities/Linux/ZeroPlaneF`

## Core rules

- Prefer rebuilding from `.geo` after geometry edits instead of patching an inherited unstable `.rea`.
- For 2D runs in this repo, use `-z2`.
- For non-VIV style runs here, use `FFX` drive-force edits.
- Use `Given` with zero initial velocity for fresh runs unless an existing case explicitly requires restart mode.
- Break long workflows into smaller steps on CCV; SSH/exec wrappers may report failure after successful substeps.

## Common parameter patch used in these cases

- `KINVIS -> 10.0` for the straight / bifurcation family used in this session
- `DT -> 1e-4`
- short check: `NSTEPS=20`, `HISSTEP=1`, `IOSTEP=1`
- production: `NSTEPS=400` or `2000`, `HISSTEP=20`, `IOSTEP=20` or `100`
- replace initial `u = 1.0` with `u = 0.0` for fresh starts when needed
- keep `Restart` blocks out of fresh runs

## Geometry-edit guidance

- **Straight periodic duct**: keep periodic sides symmetric in `x`, use physical curves 5/6 for periodic sides, and stay within mesh-size limits when requested.
- **Aneurysm radius studies**: edit the geometry parameter (`Ra`) directly; regenerate mesh and `.rea` from scratch.
- **Bifurcation long inlet/outlet**: move only the outer side-wall points and leave the center bifurcation/island region unchanged.

## Postprocessing

- `ZeroPlaneF -r case.rea chkfile.chk -o chkfile.dat` often works without a `.map` file in these 2D cases.
- Treat the warning `field file may be in the wrong format for this architecture` as nonfatal if the `.dat` file is still written.

## Read next

- Read `references/session-recipes.md` for concrete case recipes.
- For island size / shifted-island studies, use the separate `nektar2p5d-bifurcation-island-sweeps` skill.
