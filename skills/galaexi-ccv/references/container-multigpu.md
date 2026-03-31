# Container + multi-GPU notes (CCV/Oscar)

Use this reference when the task involves Apptainer/NVHPC container runs, multi-rank / multi-GPU validation, or distinguishing runtime-launch problems from memory/numerical problems.

## Validated case

- `/users/zwang197/scratch/zwang/Re30K_Ma2.0_M8`

## Known working container batch patterns

### Simple in-container `mpirun`

```bash
#!/bin/bash
#SBATCH -J re30k_m8_cont_n2
#SBATCH -p 3090-gcondo
#SBATCH --nodes=1
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --gres=gpu:2
#SBATCH --gpus-per-task=1
#SBATCH -t 00:20:00
#SBATCH -o container_n2.out
#SBATCH -e container_n2.err
set -euo pipefail
cd /path/to/case
/usr/bin/apptainer exec -B /oscar/ --nv /users/zwang197/Codes/galaexi_EVM/saluja/nvhpc-container-py3 \
  bash -lc "mpirun -np 2 --bind-to none ./galaexi parameter_flexi.ini"
```

This launch pattern demonstrated that Galaexi can start inside the container and reach multi-GPU runtime, though the run may still fail later because of memory or numerics.

### Recommended 3-GPU UUID-pinned in-container `mpirun`

Use the bundled reference script:

- `references/runme.container_mpirun_uuid_3gpu.sbatch`

This version keeps `mpirun` inside the container, but assigns one GPU UUID per local MPI rank via `OMPI_COMM_WORLD_LOCAL_RANK` and `CUDA_VISIBLE_DEVICES`. It avoids the direct-`srun` MPI-init failure while still pinning ranks explicitly to GPUs.

## Stronger per-rank GPU binding

If GPU mapping is in doubt, prefer explicit UUID-based rank binding:

```bash
mapfile -t GPU_UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
cat > .rank_uuid_run.sh <<'RS'
#!/bin/bash
set -euo pipefail
lr=${SLURM_LOCALID:-0}
IFS=' ' read -r -a uuids <<< "$GPU_UUIDS_STR"
export CUDA_VISIBLE_DEVICES="${uuids[$lr]}"
echo "rank=$SLURM_PROCID local=$lr host=$(hostname) CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
exec /path/to/galaexi parameter_flexi.ini
RS
chmod +x .rank_uuid_run.sh
export GPU_UUIDS_STR="${GPU_UUIDS[*]}"
srun --mpi=pmix --ntasks=${SLURM_NTASKS} --cpus-per-task=${SLURM_CPUS_PER_TASK} bash ./.rank_uuid_run.sh
```

Use this when you need stronger proof that each rank is attached to a unique GPU.

## Log files to inspect

- `runme.container_mpirun_n2.sbatch`
- `runme.galaexi`
- `container_n2.out`
- `container_n2.err`
- `interactive_n2_smoke.out`
- `interactive_n2_smoke.err`

Scheduler checks:

```bash
squeue -u zwang197 -o '%.18i %.9P %.40j %.8T %.10M %.6D %R'
sacct -j <JOBID> --format=JobID,JobName%30,Partition,State,ExitCode,Elapsed,NodeList -X
```

## Failure signatures

### GPU OOM

Observed batch symptom:

```text
Out of memory allocating 137088000 bytes of device memory
Accelerator Fatal Error: call to cuMemAlloc returned error 2 (CUDA_ERROR_OUT_OF_MEMORY)
```

Interpretation: multi-GPU launch path is functioning; memory footprint is too large.

### No accelerator device found

Observed in a separate interactive smoke test:

```text
Accelerator Fatal Error: No accelerator device found for cudafor_acc_malloc call
```

Interpretation: smoke-test environment/device issue. Do not confuse this with a successful batch job that already reached initialization or time stepping.

### NaNs while still running

Observed runtime symptom:

- `max velocity and entropy viscosity: NaN`
- body forces become `NaN`
- job continues stepping

Interpretation: launcher is no longer the main problem; this points to numerical/input instability.

## Memory reduction order

When the immediate goal is to verify multi-GPU runtime rather than preserve every output product, reduce memory in this order:

1. Disable time averaging:
   - `WriteTimeAvgFiles = F`
   - `CalcTimeAverage   = F`
2. Reduce `NAnalyze`
3. If still needed, reduce `N`

Validated observations:

- Lowering only `NAnalyze` from 9 to 5 was not enough to avoid OOM.
- Disabling time averaging let the 2-GPU run get beyond the previous immediate OOM point and enter time stepping.

## Mach-number changes while keeping Reynolds number fixed

If the user wants to change Mach number while keeping Reynolds-number inputs fixed, preserve:

- `rho`
- `U`
- `Mu0`

and modify the reference-pressure / thermodynamic side instead of changing velocity.

Validated corrected edit:

```ini
RefState          = (/1.,1.0,0.,0.,0.079365079365/)
```

## Acknowledgements to preserve

Thanks to:

- Saluja, Singh (`prabhjyot_saluja@brown.edu`)
- Shukla, Khemraj (`khemraj_shukla@brown.edu`)

Use concise wording such as:

> Thanks to Saluja/Singh for help with the GALAEXI CCV container and multi-GPU workflow debugging.
