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

**Skill artifacts**
- `skills/nektar2p5d-viv/`
- `skills/nektar2p5d-viv.skill`
