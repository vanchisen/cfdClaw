---
name: nekrs-ccv
description: Compile and run nekRS on Brown CCV/Oscar with NVHPC+MPI, including module setup, build.sh/nrsconfig usage, run-folder staging from Example files, sbatch submission, and quick runtime diagnostics. Use when building nekRS on CCV or preparing/executing nekRS GPU jobs.
---

# nekRS on CCV

Use this skill for practical nekRS build/run workflow on CCV.

## Quick workflow
1. Go to nekRS source root (example: `/users/zwang197/Codes/nekRS-23.avm`).
2. Load CCV modules and compiler env.
3. Configure with `build.sh` (or `nrsconfig` directly).
4. Build with `make -j`.
5. Stage case files (`.re2`, `.par`, `.udf/.usr/.oudf`, run script) in a run folder.
6. Submit with `sbatch runme.nekRS`.
7. Check `squeue`, output/error logs, and cancel if only smoke testing.

## Compile on CCV
Typical sequence:

```bash
module purge
module load nvhpc/25.5-ar5i
module load hpcx-mpi/2.25.1s-le4f
module load cuda
module load cmake

export CC=mpicc
export CXX=mpicxx
export FC=mpifort
export OMPI_CC=nvc
export OMPI_CXX=nvc++
export OMPI_FC=nvfortran

source build.sh
make -j 4
```

Notes:
- In this repo README note, the command typo `buil.sh` should be `build.sh`.
- Existing builds may already place binary at `build/nekrs`.

## Run-folder staging
Create a clean run directory and copy needed files from `Example/` or your case source.

Required case assets:
- mesh: `*.re2`
- parameters: `*.par`
- user code: `*.udf` / `*.usr` / `*.oudf` (as needed)
- job script: `runme.nekRS`

Then submit:

```bash
sbatch runme.nekRS
```

## Runtime checks
```bash
squeue -j <JOBID> -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"
tail -n 40 gpu.out
 tail -n 40 gpu.err
```

If validating startup only:
```bash
scancel <JOBID>
```

## Common issues
- Wrong script name in notes (`buil.sh` typo).
- Missing case file(s) in run directory (especially `.re2`/`.par`/UDF).
- Module/toolchain mismatch between configure and run environments.
- GPU partition/QoS mismatch causing long pending queues.

## References
- `references/ccv-run-checklist.md`
