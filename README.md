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
- `Flags/Linux.inc` is machine-dependent; on a different computer/cluster, compiler/toolchain settings may need to be changed before build works (`CC/CXX/FC`, MPI wrappers, flags, and lib paths).
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

### `post.sh` / `ZeroPlaneF` note on CCV
- `ZeroPlaneF` in this workflow expects **`-m`** (lowercase) for map file.
- If `post.sh` uses `-M` (uppercase), conversion can fail with:
  - `nek2tec: unknown option -- M`
- Also load runtime env before conversion:
  - `source ~/modules_2026`

Working conversion form:

```bash
../Utilities/Linux/ZeroPlaneF -r cyl.rea -m cyl_1.map cyl_1.chk -o cyl_1.dat
```

Latest-file conversion pattern:

```bash
source ~/modules_2026
chk=$(ls -1t cyl*.chk | head -n1)
map=$(ls -1t cyl*.map | head -n1)
out=${chk%.chk}.dat
../Utilities/Linux/ZeroPlaneF -r cyl.rea -m "$map" "$chk" -o "$out"
```

**Skill artifacts**
- `skills/nektar2p5d-viv/`
- `skills/nektar2p5d-viv.skill`

## Galaexi on CCV (OpenClaw skill)
This repo now includes an OpenClaw skill for compiling and running **Galaexi** on Brown CCV/Oscar.

**What it covers**
- NVHPC + HPCX module setup on CCV
- Configure/build workflow (`cmake_nvhpc.sh` and MPI variant usage)
- Preparing clean run folders from `Example/` inputs
- Submitting GPU jobs with `sbatch runme.galaexi`
- Quick runtime validation (`squeue`, `gpu.out`, `gpu.err`) and optional early stop after smoke-check

**Skill artifacts**
- `skills/galaexi-ccv/`
- `skills/dist/galaexi-ccv.skill`

## nekRS on CCV (OpenClaw skill)
This repo now includes an OpenClaw skill for compiling and running **nekRS** on Brown CCV/Oscar.

**What it covers**
- NVHPC + HPCX + CUDA module setup
- Configure/build via `build.sh` + `make`
- Run-folder staging for case files (`.re2`, `.par`, UDF/USR/OUDf)
- Job submission with `sbatch runme.nekRS`
- Runtime smoke-check and quick diagnostics (`squeue`, `gpu.out`, `gpu.err`)

**Skill artifacts**
- `skills/nekrs-ccv/`
- `skills/dist/nekrs-ccv.skill`

## FLEXI 3D -> 2D(one-layer-z) restart interpolation note

When generating an initial condition for a 2D-like case whose mesh is still 3D with one z-layer (e.g., `z=const`), use **`posti_swapmesh`** instead of copying/slicing `DG_Solution` directly.

### Why
- Source and target meshes are different.
- Direct z-slice copy is not mesh-aware and can produce inconsistent fields.
- `posti_swapmesh` performs proper mesh-to-mesh interpolation and projection.

### Working setup used
- Source restart: `~/Works/Compressible/Re5K_Ma2.0/restart.h5`
- Target mesh/case: `~/Works/Compressible/Re5K_Ma2_2D/`
- Parameter file: `swapmesh_ma2_3d_to_2d.ini`
- Binary that worked: `~/Works/flexi_new/build_swapmesh/bin/posti_swapmesh`

### Build `posti_swapmesh` (if needed)
```bash
cd ~/Works/flexi_new
rm -rf build_swapmesh && mkdir build_swapmesh && cd build_swapmesh
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DPOSTI=ON -DPOSTI_SWAPMESH=ON -DPOSTI_VISU=OFF \
  -DLIBS_USE_MPI=OFF -DLIBS_BUILD_HDF5=ON \
  -DFLEXI_FV=BLEND -DFLEXI_NODETYPE=GAUSS-LOBATTO
cmake --build . --target posti_swapmesh -j 8
```

### Run interpolation
```bash
cd ~/Works/Compressible/Re5K_Ma2_2D
~/Works/flexi_new/build_swapmesh/bin/posti_swapmesh \
  swapmesh_ma2_3d_to_2d.ini \
  ../Re5K_Ma2.0/restart.h5
```

### Known pitfall
Older/incompatible `posti_swapmesh` binaries can fail with:
- `Unknown option: FV_CellType`

If that appears, switch to a compatible binary (as above) and rerun.
