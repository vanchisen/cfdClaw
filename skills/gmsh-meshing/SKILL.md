---
name: gmsh-meshing
description: Gmsh-based meshing workflows for CFD. Use for creating/refining 2D/3D meshes, setting size fields, assigning physical groups/BC tags, exporting .msh, or adapting template .geo files.
---

# Gmsh Meshing

## Quick workflow
1) Start from a template in `assets/templates/` (cyl/ellipse/elliSqua/pipe_curve).
2) Edit geometry + parameters (dimensions, lc, refine regions).
3) Define **Physical Groups** for BC tags.
4) Mesh + export: `gmsh model.geo -2 -format msh2 -o model.msh`.

## Tasks
### A) Generate a mesh from a template
- Copy a template from `assets/templates/` into your working dir.
- Adjust geometry + `lc`.
- Ensure **Physical** tags exist (see `references/physical-groups.md`).

### A.1) Curved branch Y‑pipe (recent practice)
- Start from `pipe_Y_hex.geo` and keep **Transfinite + Recombine** blocks intact.
- For curved branches, parameterize the branch centerline as a circular arc in the XY plane:
  - `theta_branch` = branch half‑angle (e.g. `Pi/4` for 90° between branches)
  - `Rbend` controls arc length: `L_arc = Rbend * theta_branch`
- To **lengthen branches**, update **Rbend** (not just `Lbranch`), e.g. `Rbend = 18/(Pi/4) ≈ 22.918`.
- Use splines for **branch axial connectors** (replace straight `Line()` with `Spline()` using a midpoint control point) to preserve block topology.
- Keep **Physical groups** unchanged and export as MSH2 (`Mesh.MshFileVersion = 2.2`).

### B) Add refinement near walls/features
- Use **Distance + Threshold** size fields (see `references/size-fields.md`).

### C) Export for downstream solvers
- Prefer `msh2` unless your solver supports `msh4`.
- See `references/export-formats.md`.

### D) Zhaojie duct_h1 periodic setup (gmsh2rea.py strict pairing)
- Use `references/zhaojie-duct-periodic-gmsh2rea.md` when preparing
  `Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.geo`.
- Follow the rule used by `gmsh2rea.py` for y-periodic groups (phys 5/6):
  **paired side midpoints must satisfy `x_left + x_right = 0` and `y_left = y_right`**.
- For the normalized case, scale the periodic side height to `1.0` and keep periodic sides symmetric in `x`.

## References
- `references/gmsh-basics.md`
- `references/size-fields.md`
- `references/physical-groups.md`
- `references/export-formats.md`
- `references/zhaojie-duct-periodic-gmsh2rea.md`

## Assets
- `assets/templates/cyl.geo`
- `assets/templates/ellipse.geo`
- `assets/templates/elliSqua.geo`
- `assets/templates/pipe_curve.geo`
