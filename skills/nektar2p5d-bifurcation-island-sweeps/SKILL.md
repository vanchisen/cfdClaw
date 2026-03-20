---
name: nektar2p5d-bifurcation-island-sweeps
description: Bifurcation island size sweeps and shifted-island studies for the Nektar2.5D bifurcation case family. Use when scaling the middle island, shifting the island upward, checking mesh-valid parameter limits, or exporting final .dat files for bifurcation island variants.
---

# Bifurcation Island Sweeps

## Use this workflow

- Start from the bifurcation base geometry.
- Change only island points 28-35.
- Rebuild `.msh` with `gmsh -2 -format msh2`.
- Rebuild `.rea` with `gmsh2rea.py`.
- Make `*_shortchk.rea` and `*_run.rea`.
- Run short check first.
- Run production case.
- Export the latest checkpoint with `ZeroPlaneF`.

## Scaling studies

- Scale only island points 28-35 around the island center.
- Stable completed scale cases in this session: `0.3x`, `0.5x`, `0.8x`, `1.2x`, `1.5x`.
- Invalid geometry: `2.0x` due to self-intersection / gmsh edge recovery failure.

## Shift studies based on 0.8x island

- Use the successful `0.8x` geometry as the base.
- Shift only island points 28-35 upward in `y`.
- Valid / meshable in this session: `+0.1`, `+0.2`, `+0.3`, `+0.4`, `+0.5`.
- Invalid: `+1.0`, `+1.5` due to collision with the outer boundary.

## Failure mode rule

If gmsh reports line intersections or edge recovery failure after a scale/shift edit, treat that geometry as invalid rather than forcing the run.

## Read next

- Read `references/island-study-index.md` for the study summary and file naming conventions.
