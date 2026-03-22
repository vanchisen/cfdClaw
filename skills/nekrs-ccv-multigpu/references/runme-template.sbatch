#!/bin/bash
#SBATCH --time=20:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=<N>
#SBATCH --cpus-per-task=1
#SBATCH --mem=192G
#SBATCH -J <CASE>
#SBATCH -p 3090-gcondo
#SBATCH --gres=gpu:<N>
#SBATCH -o gpu.out
#SBATCH -e gpu.err

set -euo pipefail

module purge
module load nvhpc/25.5-ar5i
module load hpcx-mpi/2.25.1s-le4f
module load cuda
module load cmake

export NEKRS_HOME=$HOME/.local/nekrs
export PATH=$NEKRS_HOME/bin:$PATH

# CCV stack here is not GPU-aware MPI for this nekRS build
export NEKRS_GPU_MPI=0

# Case-local caches
export NEKRS_CACHE_DIR=$PWD/.cache_runs/nekrs
export OCCA_CACHE_DIR=$PWD/.cache_runs/occa
rm -rf "$PWD/.cache_runs"

# Keep expected MPI libs first
export LD_LIBRARY_PATH=/oscar/rt/sw/external/hpcx-mpi/2.25.1/lib:${LD_LIBRARY_PATH:-}

echo "mpirun=$(which mpirun)"
echo "nekrs=$(which nekrs)"
echo "NEKRS_GPU_MPI=$NEKRS_GPU_MPI"

mpirun -np <N> nekrs --setup cyl.par
