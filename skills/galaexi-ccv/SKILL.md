---
name: galaexi-ccv
description: Build and run Galaexi on Brown CCV/Oscar with NVHPC+MPI, including module setup, CMake configure/build, GPU sbatch job setup, Apptainer/NVHPC container runs, multi-rank multi-GPU launches, and quick runtime checks. Use when compiling Galaexi, preparing run folders from Example inputs, submitting jobs, validating multi-GPU startup, reducing GPU memory footprint, or diagnosing startup/runtime issues on CCV.
---

# Galaexi on CCV

Use this skill for the practical compile/run workflow of Galaexi on CCV.

## Quick workflow
1. Enter code root (e.g. `/users/zwang197/Codes/galaexi_EVM`).
2. Load CCV modules and compiler env.
3. Configure with the repo script (`cmake_nvhpc.sh` or MPI variant).
4. Build and confirm `build/bin/galaexi` exists.
5. Create a clean run folder, copy binary + `.ini` + mesh + run script.
6. Submit with `sbatch runme.galaexi`.
7. Verify startup via `squeue`, `gpu.out`, `gpu.err`.

## Compile steps (CCV)
From the Galaexi repo root:

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

source cmake_nvhpc.sh
make -j 4
```

If using explicit MPI build script in this repo, use `source cmake_mpi_nvhpc.sh` instead.

## Run-folder preparation
Use a separate run directory (typically under scratch):

```bash
RUN=/users/zwang197/scratch/zwang/galaexi_runs/<case_name>
mkdir -p "$RUN"
cp build/bin/galaexi "$RUN/"
cp Example/parameter_flexi.ini "$RUN/"
cp Example/DARU_mesh.h5 "$RUN/"
cp Example/runme.galaexi "$RUN/"
cd "$RUN"
sbatch runme.galaexi
```

## Runtime checks
- Queue/state:
```bash
squeue -j <JOBID> -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"
```
- Output tail:
```bash
tail -n 40 gpu.out
tail -n 40 gpu.err
```
- If only sanity-checking startup, cancel once logs look healthy:
```bash
scancel <JOBID>
```

## Container + multi-GPU workflow

When the user is running inside an Apptainer/NVHPC container or trying to prove that Galaexi can run on multiple GPUs, read `references/container-multigpu.md`.

Key takeaways from the validated CCV case:

- A 2-rank / 2-GPU containerized launch can reach initialization and time stepping on CCV.
- `CUDA_ERROR_OUT_OF_MEMORY` means the launch path is alive but per-GPU memory is too high.
- A separate `No accelerator device found` smoke-test failure should not be confused with a batch run that already reaches time stepping.
- If the code keeps stepping but reports `NaN` values, treat that as a numerical/input issue instead of a launcher failure.
- To reduce memory without changing the launch path first, disable time averaging before reducing polynomial order.

## Common issues
- **Binary missing**: rebuild and verify `build/bin/galaexi`.
- **Input not found**: run folder must include mesh + ini expected by run script.
- **Module mismatch message in `gpu.err`**: check loaded toolchain (`module list`) and keep NVHPC/HPCX consistent with build.
- **Job pending for long time**: check partition/QoS/resource request against available GPUs.
- **Immediate container OOM**: disable time averaging first, then reduce `NAnalyze`, then consider reducing `N`.
- **NaNs during stepping**: inspect `RefState`, initialization consistency, EVM/FV settings, and restart/mesh compatibility.

## References
- `references/ccv-job-template.md`
- `references/container-multigpu.md`
