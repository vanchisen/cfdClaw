---
name: nekrs-ccv-multigpu
description: Compile, launch, and troubleshoot nekRS on Brown CCV (Oscar) with Slurm and multi-GPU jobs. Use when building `~/Codes/nekRS-23.avm`, creating/updating `runme.nekRs`, selecting MPI rank/GPU counts, handling cache issues, or debugging bus errors in `oogs::setup`/`PMPI_Waitall`.
---

# nekRS on CCV (multi-GPU)

Use this skill for nekRS workflows on Brown CCV with Slurm.

## Build workflow (from project ReadMe)

In `~/Codes/nekRS-23.avm`:

1. Load modules in this order:
   - `module purge`
   - `module load nvhpc/25.5-ar5i`
   - `module load hpcx-mpi/2.25.1s-le4f`
   - `module load cuda`
   - `module load cmake`
2. Set compiler wrappers:
   - `export CC=mpicc`
   - `export CXX=mpicxx`
   - `export FC=mpifort`
   - `export OMPI_CC=nvc`
   - `export OMPI_CXX=nvc++`
   - `export OMPI_FC=nvfortran`
3. Build:
   - `source build.sh`
   - `make -j 4`

## Run workflow (Slurm)

1. Run via `sbatch` on compute nodes (not login nodes).
2. Keep GPU count equal to MPI rank count for this workflow (`--ntasks=N`, `--gres=gpu:N`, `mpirun -np N`).
3. Set case-local cache each run:
   - `NEKRS_CACHE_DIR=$PWD/.cache_runs/nekrs`
   - `OCCA_CACHE_DIR=$PWD/.cache_runs/occa`
   - `rm -rf .cache_runs`
4. Force non-GPU-aware MPI mode on this CCV stack:
   - `export NEKRS_GPU_MPI=0`

Reason: CCV MPI here reports `mpi_built_with_cuda_support:false`; leaving `NEKRS_GPU_MPI=1` can trigger bus errors in `oogs::setup`.

## Minimal robust run script pattern

Use `references/runme-template.sbatch` as baseline.

## Troubleshooting quick map

- Symptom: bus error around `oogs::setup -> PMPI_Waitall -> ucp_*`
  - Check `NEKRS_GPU_MPI` value first; set `NEKRS_GPU_MPI=0`.
  - Wipe `.cache_runs` and rerun.
- Symptom: repeated failures after branch/toolchain changes
  - Rebuild nekRS in the same module environment used at run time.
- Symptom: startup appears slow
  - Expect long phases: `building nekInterface ...` and `JIT compiling kernels ...`.

## Monitoring commands

- `tail -f gpu.out`
- `squeue -u zwang197`
- `sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode,NodeList,TRESUsageInMax -P`

## Practical memory note

On case `DNS/A1I5`, Slurm reported `gres/gpumem=68906M` (peak aggregate for one 8-GPU run step). Use this as a rough sizing reference, not a universal limit.
