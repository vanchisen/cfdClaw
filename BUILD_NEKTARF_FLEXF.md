# Build nektarF / flexF (Nektar2.5D)

Source tree:
- `/users/zwang197/Works/NeuroSEM/URANS/Nektar2.5D`

This repo uses a classic MakeNek/Makefile.lns style build, driven by small `compile` scripts in subfolders.

## One-shot build (as encoded in `build.sh`)

From the Nektar2.5D root:

```bash
cd /users/zwang197/Works/NeuroSEM/URANS/Nektar2.5D

# 1) FFT library
cd rfftw
make clean
make
cp libfftw.a ../Hlib/Linux/

# 2) Vec library
cd ../Veclib/
source compile
cp libvec.a ../Hlib/Linux/

# 3) Hybrid library
cd ../Hlib/Linux/
source compile

# 4) nektarF (flow solver without moving boundary)
cd ../../SPM_Thermo/Linux/
source compile

# 5) flexF (VIV / moving boundary)
cd ../../SPM_Thermo/Linux.Map
source compile
```

## What each `compile` script does

### `Veclib/compile`

```bash
make OPTM=1
```

### `Hlib/Linux/compile`

```bash
rm libhybrid*
make PARALLEL=1 dbx
make PARALLEL=1 mopt
make PARALLEL=1 opt
make dbx
make mopt
make mopt
```

### `SPM_Thermo/Linux/compile` (builds `nektarF`)

```bash
make PARALLEL=1 mopt THERMO=0 NATURAL_CONVECTION=0 SPM=0 XMLRPC=0
```

### `SPM_Thermo/Linux.Map/compile` (builds `nektarF` + `flexF` with MAP)

```bash
make PARALLEL=1 mopt THERMO=0 NATURAL_CONVECTION=0 SPM=0 XMLRPC=0 MAP=1 ADDONS="TMAP SL"
```

## Outputs (examples)

- `SPM_Thermo/Linux/nektarF`
- `SPM_Thermo/Linux.Map/nektarF`
- `SPM_Thermo/Linux.Map/flexF`
- `Hlib/Linux/libhybrid*.a`
