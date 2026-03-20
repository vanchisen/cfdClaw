# Session recipes

## Brown CCV toolchain

- Repo root: `/users/zchai5/data/zchai5/Data2026/Nektar2.5D_OpenClaw/cfdClaw`
- Mesh conversion: `/users/zchai5/data/zchai5/Data2026/Nektar2.5D_OpenClaw/Nektar2.5D/Examples/gmsh2rea.py`
- Solver: `/users/zchai5/data/zchai5/Data2026/Nektar2.5D_OpenClaw/Nektar2.5D/SPM_Thermo/Linux/nektarF`
- Tecplot export: `/users/zchai5/data/zchai5/Data2026/Nektar2.5D_OpenClaw/Nektar2.5D/Utilities/Linux/ZeroPlaneF`

Set:
```bash
source ~/.bashrc
export LD_LIBRARY_PATH=/users/zchai5/miniconda3/lib:$LD_LIBRARY_PATH
```

## Straight periodic case

- Create a transfinite/recombined rectangular duct.
- Use physical curves 5/6 for periodic sides.
- Convert with `gmsh2rea.py`.
- Patch into short-check + run `.rea` files.
- Export chosen checkpoints with `ZeroPlaneF`.

## Aneurysm case

- Edit aneurysm radius directly in geometry (`Ra`).
- Rebuild mesh and `.rea` from scratch after each `Ra` change.
- Stable outputs in this session existed for `Ra = 1.0`, `3.0`, and `4.0`.

## Bifurcation long case

- Start from `bifurcation/duct.geo`.
- Extend only outer inlet/outlet side-wall points.
- Keep center bifurcation region unchanged.
