#!/bin/bash
#SBATCH -J re30k_m8_cont_n3_mpiuuid
#SBATCH -p a6000-gcondo
#SBATCH --nodes=1
#SBATCH --ntasks=3
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --gres=gpu:3
#SBATCH --gpus-per-task=1
#SBATCH -t 00:20:00
#SBATCH -o container_n2.out
#SBATCH -e container_n2.err
set -euo pipefail
cd /users/zwang197/scratch/zwang/Re30K_Ma2.0_M8

mapfile -t GPU_UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
echo "Detected ${#GPU_UUIDS[@]} GPU UUID(s):"
for i in "${!GPU_UUIDS[@]}"; do echo "[$i] ${GPU_UUIDS[$i]}"; done
export GPU_UUIDS_STR="${GPU_UUIDS[*]}"

/usr/bin/apptainer exec -B /oscar/ --nv /users/zwang197/Codes/galaexi_EVM/saluja/nvhpc-container-py3 bash -lc '
  set -euo pipefail
  cd /users/zwang197/scratch/zwang/Re30K_Ma2.0_M8
  cat > .rank_uuid_run_inside_container.sh <<"RS"
#!/bin/bash
set -euo pipefail
rank=${OMPI_COMM_WORLD_LOCAL_RANK:-0}
IFS=" " read -r -a uuids <<< "$GPU_UUIDS_STR"
export CUDA_VISIBLE_DEVICES="${uuids[$rank]}"
echo "inside-container rank=${OMPI_COMM_WORLD_RANK:-?} local_rank=${rank} host=$(hostname) CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
exec ./galaexi parameter_flexi.ini
RS
  chmod +x .rank_uuid_run_inside_container.sh
  mpirun -np 3 --bind-to none bash ./.rank_uuid_run_inside_container.sh
'
