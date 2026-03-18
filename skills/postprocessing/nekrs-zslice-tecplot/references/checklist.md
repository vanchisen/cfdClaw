# Checklist: nekRS mid-z slice to Tecplot

1. Confirm case has `*.nek5000` (usually `avgcyl.nek5000`).
2. Run:
   - `pvpython scripts/toyota_midz_to_vtk.py <case_dir> <case_dir>/avgcyl_midZ_latest.vtk`
3. Convert:
   - `python3 /users/zwang197/Works/NeuroSEM/Toyota/runs/vtk_polydata_to_tecplot_dat.py <vtk> <dat>`
4. Verify `.dat` header has:
   - `DATAPACKING=POINT`
   - `ZONETYPE=FETRIANGLE`
5. Report paths for both `.vtk` and `.dat`.
