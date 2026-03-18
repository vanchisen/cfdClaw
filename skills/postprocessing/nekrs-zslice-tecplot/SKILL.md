---
name: nekrs-zslice-tecplot
description: Extract middle-z slices from nekRS outputs (`*.nek5000`) and convert to Tecplot ASCII FEM (`.dat`). Use when user asks for z-slice/mid-plane extraction from nekRS/Toyota cases and wants ParaView/VTK/Tecplot outputs.
---

# nekRS z-slice → Tecplot

## Quick workflow
1. Use ParaView `pvpython` to load `<case>/avgcyl.nek5000` (or other `*.nek5000`).
2. Move to the latest available timestep.
3. Slice with plane normal `[0,0,1]` at middle z (`zmid = (zmin+zmax)/2`).
4. Save as legacy VTK polydata (`*.vtk`).
5. Convert VTK to Tecplot ASCII FEM (`*.dat`) using converter script.

## Commands

```bash
# 1) Extract mid-z VTK
pvpython scripts/toyota_midz_to_vtk.py <case_dir> <out_vtk>

# 2) Convert to Tecplot ASCII FEM
python3 /users/zwang197/Works/NeuroSEM/Toyota/runs/vtk_polydata_to_tecplot_dat.py <out_vtk> <out_dat>
```

## Expected Tecplot format
The resulting `.dat` should include a zone header like:
- `DATAPACKING=POINT`
- `ZONETYPE=FETRIANGLE`

This is Tecplot ASCII FEM form.

## Notes
- Default output naming convention:
  - `avgcyl_midZ_latest.vtk`
  - `avgcyl_midZ_latest.dat`
- Typical Toyota cases have bounds `z:[0, 6.4]`, so `zmid≈3.2`.
- If user asks for non-middle slice, override origin `z` in script.

## References
- `references/checklist.md`
