# nekRS CCV run checklist

Use this pre-submit checklist for reliable runs.

## Before build
- Confirm modules: `nvhpc`, `hpcx-mpi`, `cuda`, `cmake`
- Confirm compiler env vars point to MPI wrappers (`mpicc/mpicxx/mpifort`)

## Before submit
- `nekrs` binary exists (`build/nekrs` or copied into run folder)
- Run folder contains:
  - `*.re2`
  - `*.par`
  - user source (`*.udf` or `*.usr`/`*.oudf`) if case requires it
  - `runme.nekRS`

## After submit
- `squeue -j <JOBID>` shows job enters `R` eventually
- `gpu.out` advances beyond startup (no immediate abort)
- `gpu.err` has no fatal library/module/runtime errors

## Quick stop after smoke test
If the objective is startup validation only:

```bash
scancel <JOBID>
```
