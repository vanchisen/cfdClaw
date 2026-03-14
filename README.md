# cfdClaw

A project on using **OpenClaw** to assist learning and developing **CFD** skills.

## Focus Areas
- Meshing workflows
- Incompressible flows
- Compressible flows
- Multi‑phase flows
- Turbulence modeling
- Post‑processing and visualization

## Purpose
Capture practical notes, examples, and workflows for learning and applying CFD with OpenClaw assistance.

## Gmsh Meshing (OpenClaw skill)
This repo ships a packaged OpenClaw skill for Gmsh-based meshing workflows.

**What it covers**
- Building 2D/3D meshes from templates
- Transfinite + recombine workflows for fully hex meshes
- Physical groups / BC tagging
- Size fields and local refinement
- Export to `.msh` (default MSH2 unless otherwise needed)

**Skill artifact**
- `skills/gmsh-meshing.skill`

**Example usage**
- “Generate a mesh from `assets/templates/pipe_curve.geo` with finer wall resolution.”
- “Update a Y‑pipe `.geo` to use curved branches and keep hex transfinite topology.”
- “Add Distance+Threshold size field near the wall and export MSH2.”

**Notes**
- Curved‑branch Y‑pipe workflows use an arc‑length relation: `L_arc = Rbend * theta_branch`.
- For longer branches, update **Rbend** (not just `Lbranch`) to change the true arc length.

## Nektar2.5D VIV (OpenClaw skill)
This repo also ships an OpenClaw skill for the in-house **Nektar2.5D** VIV workflow.

**What it covers**
- Compile order for Nektar2.5D components
- Cylinder-case VIV run workflow (`generateInput.sh`, `runme`, `post.sh`)
- Practical `cyl.rea` parameter editing guidance
- Forced vs free VIV setup hints
- Runtime checks and common startup failure patterns

### CCV notes learned in practice
- Build in strict ReadMe order:
  1. `GS/`
  2. `rfftw/`
  3. `Veclib/`
  4. `Hlib/Linux/`
  5. `SPM_Thermo/Linux/`
  6. `Utilities/Linux/`
- If scratch tarball build fails on CCV, fallback-copy:
  - `~/Codes/Nektar2.5D/Flags/Linux.inc` -> `<current>/Flags/Linux.inc`
- For **2D simulation**, this workflow uses **`-z2`**.

### `.rea` file integrity rules (important)
- `STASTEP` must be set (or runtime may abort with `forget to set STASTEP !`).
- If parameters are added/removed, update line-4 count:
  - `N PARAMETERS FOLLOW`
- Count is the number of lines between:
  - `PARAMETERS FOLLOW`
  - `Lines of passive scalar data follows...`

### Common 2D setup used in this workflow
- `NZTOT=2`
- `LZ=0.01`
- `MODES=3` (2nd-order SEM)
- `LQUAD=5`
- `MQUAD=5`
- baseline `DT=0.002`, then tune by CFL

### Initial condition convention
- Fresh run: `Given` (typically zero fields)
- Restart run:
  - rename `*.chk` -> `*_old.rst`
  - rename `*.map` -> `*.map.rst`
  - switch `.rea` IC mode to `Restart`

### `*.dog` output format reference
From `SPM_Thermo/src/map.C` (`writedog2`):
- Default (13 cols):
  `time, dx, dy, dzx, dzy, vx, vy, ax, ay, fx, fy, basep, i`
- If `D_SCR` is enabled (14 cols):
  inserts `old_static_map` after `dx`.

**Skill artifacts**
- `skills/nektar2p5d-viv/`
- `skills/nektar2p5d-viv.skill`
