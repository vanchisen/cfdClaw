# GALAEXI on CCV: MPI toolchain + `mpirun -np 6` run notes

Last updated: 2026-03-23

## Goal
Run case:

- `/users/zwang197/scratch/zwang/Re30K_Ma2.0_M8`

with:

- `mpirun -np 6 ./galaexi parameter_flexi.ini`

reliably (true MPI decomposition, avoid false single-domain/OOM behavior).

---

## 1) Working local MPI toolchain build (NVHPC-compatible)

CCV module-provided MPI stacks can fail with NVFORTRAN Fortran module compatibility (`MPI_Fortran_WORKS` / `mpi.mod` issues).
A working path is to build OpenMPI locally with NVHPC compilers.

### Build OpenMPI 4.1.8

```bash
module purge
module load nvhpc/25.5-ar5i
module load cuda
module load cmake

cd /users/zwang197/Codes/local
curl -L https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.8.tar.gz -o openmpi-4.1.8.tar.gz
rm -rf openmpi-4.1.8
mkdir -p openmpi-4.1.8
tar -xzf openmpi-4.1.8.tar.gz -C /users/zwang197/Codes/local
cd /users/zwang197/Codes/local/openmpi-4.1.8

export CC=nvc
export CXX=nvc++
export FC=nvfortran

./configure \
  --prefix=/users/zwang197/Codes/local/openmpi-nvhpc \
  --disable-mpi-java \
  --enable-mpi-fortran=all \
  --enable-mca-no-build=fs-gpfs

make -j 8
make install
```

### Validate wrappers

```bash
/users/zwang197/Codes/local/openmpi-nvhpc/bin/mpifort -show
```

Expected pattern includes local prefix and Fortran MPI libs:

- `.../openmpi-nvhpc/include`
- `.../openmpi-nvhpc/lib`
- `-lmpi_usempif08 -lmpi_usempi_ignore_tkr -lmpi_mpifh -lmpi`

---

## 2) GALAEXI build against the local MPI

Use local OpenMPI wrappers explicitly.

```bash
module purge
module load nvhpc/25.5-ar5i
module load cuda
module load cmake

export OMPI_HOME=/users/zwang197/Codes/local/openmpi-nvhpc
export PATH=$OMPI_HOME/bin:$PATH
export LD_LIBRARY_PATH=$OMPI_HOME/lib:${LD_LIBRARY_PATH:-}

# Avoid C-wrapper/compiler mismatch issues during dependent builds
export OMPI_CC=gcc
export OMPI_CXX=g++
export OMPI_FC=nvfortran

export CC=mpicc
export CXX=mpicxx
export FC=mpifort

cd /users/zwang197/Codes/galaexi_EVM
rm -rf build_mpi_gpu
mkdir build_mpi_gpu
cd build_mpi_gpu

cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_Fortran_COMPILER=${FC} \
  -DCMAKE_C_COMPILER=mpicc \
  -DCMAKE_CXX_COMPILER=mpicxx \
  -DLIBS_USE_MPI=ON \
  -DLIBS_BUILD_HDF5=ON \
  -DLIBS_USE_OPENMP=ON \
  -DOpenMP_C_FLAGS=-mp \
  -DOpenMP_CXX_FLAGS=-mp \
  -DOpenMP_Fortran_FLAGS=-mp \
  -DFLEXI_NODETYPE=GAUSS-LOBATTO \
  -DFLEXI_SPLIT_DG=ON \
  -DFLEXI_FV=BLEND \
  -DFLEXI_UNITTESTS=OFF \
  -DFLEXI_PARABOLIC=ON \
  -DLIBS_BUILD_MATH_LIB=ON \
  -DLIBS_BUILD_MATH_LIB_VENDOR=LAPACK \
  -DFLEXI_2D=OFF \
  -DFLEXI_EDDYVISCOSITY=ON

make -j 8
```

---

## 3) Runtime script for `mpirun -np 6`

Example `runme.galaexi` in case directory:

```bash
#!/bin/bash
#SBATCH --time=36:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=6
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH -J gpu1
#SBATCH -p 3090-gcondo
#SBATCH --gres=gpu:6
#SBATCH --gpus-per-task=1
#SBATCH -o gpu.out
#SBATCH -e gpu.err

set -euo pipefail
module purge
module load nvhpc/25.5-ar5i
module load cuda

export OMPI_HOME=/users/zwang197/Codes/local/openmpi-nvhpc
export PATH=$OMPI_HOME/bin:$PATH
export LD_LIBRARY_PATH=$OMPI_HOME/lib:${LD_LIBRARY_PATH:-}
export OMPI_CC=gcc
export OMPI_CXX=g++
export OMPI_FC=nvfortran

mpirun -np 6 ./galaexi parameter_flexi.ini
```

Submit:

```bash
sbatch runme.galaexi
```

---

## 4) Critical diagnostics

- If logs show repeated `nSides, MPI = 0` per rank, MPI decomposition is not truly active for the case workflow.
- CUDA OOM in that situation does **not** necessarily mean 6 GPUs are insufficient; it may indicate decomposition/binding path mismatch.
- If runtime errors show `Illegal instruction`, rebuild `galaexi` on a compute node in the target partition to avoid ISA mismatch between build host and runtime host.

---

## 5) Quick monitor commands

```bash
squeue -j <JOBID> -o "%.18i %.2t %.10M %.10l %R"
sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode
tail -f gpu.out
tail -f gpu.err
```
