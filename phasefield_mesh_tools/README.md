# PhaseField Mesh Tools (Python)

This folder will contain Python ports of the legacy C++ mesh conversion pipeline:

- `gmsh2grd`: Gmsh `.msh` → custom `.grd`
- `gg_curve` / `gg_boundary`: `.grd` + `.info` → Nektar `*.rea` (+ `*.walls`, optional `*.plt`)

We will use `meshio` to robustly read Gmsh meshes.

Next steps:
1) Implement `gmsh2grd.py` to reproduce `gmsh2grd.cc` output.
2) Add regression tests against an existing mesh (e.g. `bubble_2_fluid.msh`).
3) Then port `.grd`→`.rea` (larger effort).
