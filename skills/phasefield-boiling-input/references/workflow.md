# NonCHT phase-field boiling input generation

## File roles
- `header.txt`: simulation parameters and dimensionless constants.
- `muri_mesh.rea`: mesh/connectivity section.
- `muri_fluid.rea`: flow BC section.
- `muri_phase.rea`: phase-field BC section.
- `muri_tem.rea`: temperature BC section.
- `phase_bc.txt`, `tem_bc.txt`: supplemental BC blocks.
- `tail.txt`: initial conditions, probes, force definitions, output spec.

## Input-generation sequence
1. Select experimental case (e.g., Purdue flag 10) and target geometric scaling.
2. Update/verify `Dimen_Chan3D.py` inputs and run it.
3. Build/adjust `.geo`, mesh with Gmsh to `.msh`.
4. Convert `.msh` to `.grd` (`gmsh2grd.py`).
5. Generate `muri_mesh.rea` from `.grd` (`gg_curve_pure.py`).
6. Ensure `*.info` BC files are correct.
7. Generate `muri_fluid.rea`, `muri_phase.rea`, `muri_tem.rea` (`gg_boundary_pure.py`).
8. Assemble final REA by concatenating standard blocks.

## Validation checklist
- BC table and face counts in `.grd` look reasonable.
- `muri_*\.rea` files regenerate without missing boundary tags.
- Final assembled `.rea` includes all 8 blocks in correct order.
- If legacy binaries are available, compare pure-python outputs against binary outputs (`cmp`/`diff`).
