---
name: phasefield-boiling-input
description: Generate and update Nektar3d/phase-field flow-boiling input files for NonCHT channel cases. Use when tasks involve building `.rea` inputs from mesh + BC metadata, converting `*.msh` to `*.grd`, regenerating `muri_mesh.rea`/`muri_fluid.rea`/`muri_phase.rea`/`muri_tem.rea`, running dimensionless parameter conversion, or assembling final case files (e.g., `muri_all.rea`, `case*_all.rea`).
---

# Phase-field Boiling Input (NonCHT)

## Quick workflow
1. Work in an isolated case folder (never overwrite template baseline directly).
2. Compute/refresh nondimensional parameters with `scripts/Dimen_Chan3D.py`.
3. Convert mesh: `*.msh -> *.grd` using `scripts/gmsh2grd.py`.
4. Generate section files:
   - mesh section with `scripts/gg_curve_pure.py`
   - fluid/phase/temperature sections with `scripts/gg_boundary_pure.py`
5. Assemble final REA using:
   - `header.txt + muri_mesh.rea + muri_fluid.rea + phase_bc.txt + muri_phase.rea + tem_bc.txt + muri_tem.rea + tail.txt`
6. Validate by comparing generated files against expected/reference outputs when available.

## Commands (typical)
```bash
# 1) parameters
python3 scripts/Dimen_Chan3D.py > Dimen_Chan3D.out.txt

# 2) mesh conversion
python3 scripts/gmsh2grd.py muri_fluid --grd muri_fluid.grd

# 3) section generation (pure python ports)
python3 scripts/gg_curve_pure.py muri_fluid
python3 scripts/gg_boundary_pure.py muri_fluid
python3 scripts/gg_boundary_pure.py muri_phase
python3 scripts/gg_boundary_pure.py muri_tem

# 4) assemble
awk '1' header.txt muri_mesh.rea muri_fluid.rea phase_bc.txt muri_phase.rea tem_bc.txt muri_tem.rea tail.txt > case_noncht_all.rea
```

## Practical rules
- Keep `*.info` files as the BC source of truth:
  - `muri_fluid.info`, `muri_phase.info`, `muri_tem.info`.
- For NonCHT, fluid/phase/temperature usually share the same `.grd` mesh.
- Regenerate only what changed (mesh conversion, section generation, assembly).
- Preserve previous outputs with timestamped backups before large rewrites.

## Resources
- `references/workflow.md` for detailed sequencing and file roles.
- `scripts/` for all Python tooling bundled with this skill.
