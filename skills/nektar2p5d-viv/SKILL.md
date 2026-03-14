---
name: nektar2p5d-viv
description: In-house Nektar2.5D VIV setup, run, and troubleshooting workflow for Cylinder-style cases. Use when editing `cyl.rea`, selecting free vs forced vibration settings, setting Re/Ur/mass/damping parameters, launching `flexF`, handling restart/map files, or converting outputs for post-processing.
---

# Nektar2.5D VIV

Use this skill for Zhicheng's in-house Nektar2.5D VIV work (not Nektar++ unless explicitly requested).

## Quick workflow

1. Go to the target case directory (usually under `.../Nektar2.5D/Examples/Cylinder*`).
2. Confirm key files exist:
   - `cyl.rea`
   - mesh/restart files if restart mode is used (`cyl_old.rst`, `cyl.map.rst`)
3. Edit VIV parameters in `cyl.rea`.
4. Launch with `flexF` (for 2D runs in this workflow, **must** use `-z2`):
   - `mpirun -np 1 .../SPM_Thermo/Linux/flexF -chk -z2 -S -ou cyl.rea`
5. Tail `out` to verify progression and catch startup failures early.

## Build order (from project ReadMe)

Run `source compile` in this order:
1. `GS/`
2. `rfftw/`
3. `Veclib/`
4. `Hlib/Linux/`
5. `SPM_Thermo/Linux/`
6. `Utilities/Linux/`

### CCV-specific compile fallback

If scratch-tarball build fails on CCV, copy known-good flags from the Codes tree:

- `~/Codes/Nektar2.5D/Flags/Linux.inc` -> `<current>/Flags/Linux.inc`

In practice, some tar copies may also need restoring missing/mismatched `include/` or Veclib files from `~/Codes/Nektar2.5D`.

## Running the standard 2D example

In `Example(s)/Cylinder/`:
1. `source generateInput.sh`
2. `source runme`
3. `source post.sh`

### CCV `post.sh` note (important)

On this branch/cluster, `ZeroPlaneF` expects lowercase `-m` for map input.
If `post.sh` uses uppercase `-M`, it can fail with:
- `nek2tec: unknown option -- M`

Working conversion pattern:

```bash
source ~/modules_2026
../Utilities/Linux/ZeroPlaneF -r cyl.rea -m cyl_0.map cyl_0.chk -o cyl_0.dat
```

To convert the latest files automatically:

```bash
source ~/modules_2026
chk=$(ls -1t cyl*.chk | head -n1)
map=$(ls -1t cyl*.map | head -n1)
out=${chk%.chk}.dat
../Utilities/Linux/ZeroPlaneF -r cyl.rea -m "$map" "$chk" -o "$out"
```

## Parameter editing rules

- Treat `FORCX` and `FORCY` as primary VIV mode selectors in this branch.
- Keep edits minimal and explicit; change only requested knobs.
- For Re control in existing Cylinder cases, `KINVIS` is the primary fluid knob.
- For structural settings, commonly edited parameters are `WN`, `WNC`, `WNB`, `ZMASS`, `ZETA`.
- For prescribed harmonic motion, tune `AMPX/AMPY`, `FREQX/FREQY`, `PHITX/PHITY`.
- `STASTEP` is required in this branch; missing it triggers runtime abort (`forget to set STASTEP !`).

### Critical `.rea` integrity rule

When adding/removing parameters, update line 4 (`N PARAMETERS FOLLOW`) to match the actual number of parameter lines.

Count rule used in this workflow:
- count lines **after** `PARAMETERS FOLLOW`
- up to (but not including) `Lines of passive scalar data follows...`

For parameter meaning details, read `references/map-rea-parameter-guide.md`.

## Reliability checks after launch

- Check `out` for:
  - normal read of `cyl.rea`
  - no fatal missing-file errors
  - advancing `Time step = ...` lines
- If startup fails with restart/map errors, ensure restart files are present in run directory.
- If invoked outside original example directory, use absolute path for `flexF`.
- For 2D runs, ignore the dealiasing warning text about `-z` multiples of 4 when `-z2` is intentionally used in this workflow.

## Initial-condition conventions

- Fresh run (no restart files): use `Given` with default zero fields (`u=v=w=0`, and `t=0` if thermal).
- Restart run:
  - rename `*.chk` -> `*_old.rst`
  - rename `*.map` -> `*.map.rst`
  - switch initial condition mode in `.rea` to `Restart`.

## Expected outputs

- Runtime log: `out`
- Time histories / diagnostics: `cyl.dog`, `cyl.fce`, `cyl.cab` (case-dependent)
- Post-processing through project scripts (e.g., `post.sh`).
