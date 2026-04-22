# FLEXI/Galaexi HDF5 restart smoothing for initial conditions

This note captures a practical fallback for making a restart field much gentler when a proper modal filter path is unavailable or failing.

## When to use this

Use this when all of the following are true:
- the restart file is an HDF5 file with a `DG_Solution` dataset
- the goal is a forgiving **initial condition**, not a high-fidelity filtered solution
- aggressive smoothing is acceptable
- `filter_restart_modal.py` (or an equivalent modal filter route) is unavailable or does not work

Do **not** treat this as a numerically principled replacement for modal filtering. It is a pragmatic IC-generation hack.

## Working case

Observed file structure for:
- `/users/zwang197/scratch/zwang/Re5K_Ma2.0_Unstruct/new_solution_zmean.h5`

Dataset summary:
- dataset: `DG_Solution`
- shape: `(440928, 9, 9, 9, 5)`
- dtype: `float64`
- chunks: `None`
- compression: `None`

Interpretation:
- axis 0: elements
- axes 1-3: local DG nodal coordinates inside each element
- axis 4: variables

## Key lesson: preserve HDF5 metadata

A first attempt created a brand new `.h5` file containing only the smoothed `DG_Solution` dataset. FLEXI then aborted while reading restart metadata with:

- `Message: Attribute NodeType does not exist.`

Cause:
- the new file dropped required HDF5 attributes and possibly other objects
- the solver expects metadata such as `NodeType`

**Correct workflow:**
1. copy the original restart file to a new output path
2. overwrite only the values in `DG_Solution`
3. keep the original file/group/dataset structure and attributes intact

## Recommended smoothing strategy

For a brute-force IC smoother:
- smooth **inside each element only**
- do **not** smooth across the element axis
- do **not** smooth across the variable axis

Use a Gaussian filter with sigma tuple:
- `(0, s, s, s, 0)`

Practical values:
- `s = 1.2` : moderate
- `s = 1.8` : aggressive, recommended starting point
- `s = 2.5` : very aggressive

If variables are expected to remain bounded, clip after smoothing, e.g. to `[0, 1]`.

## Compute-node / container workflow on CCV

Do this on a compute node, not a login node.

Interactive allocation used here:
```bash
source ~/interact.sh
```

Python/HDF5 container helper:
```bash
source ~/py_singular.sh
```

`~/py_singular.sh` currently points to a container with `h5py` available.

## In-place smoothing script

Script:
- `scripts/h5_smooth_inplace_ic.py`

Example workflow:

```bash
cp new_solution_zmean.h5 new_solution_zmean_smooth_ic.h5
python3 scripts/h5_smooth_inplace_ic.py \
  new_solution_zmean_smooth_ic.h5 \
  --sigma 1.8 \
  --batch-elements 20000 \
  --clip-min 0.0 \
  --clip-max 1.0
```

What it does:
- opens the copied file in `r+`
- reads `DG_Solution` in element batches
- applies `scipy.ndimage.gaussian_filter` with sigma `(0, s, s, s, 0)`
- writes smoothed values back into the same dataset
- preserves all original metadata because the file structure is unchanged

## Why batching helps

For this case, the raw array is large:
- `440928 * 9 * 9 * 9 * 5 * 8 bytes` ≈ 13 GB

Smoothing the whole array at once can temporarily require much more memory. Batch-by-element processing avoids a large extra memory spike and is safer on shared compute nodes.

## Caveat

This method smooths only within each element. It does not remove discontinuities between neighboring elements. That is acceptable for a brute-force initial-condition hack, but it is not equivalent to a proper mesh-aware projection or DG modal filter.
