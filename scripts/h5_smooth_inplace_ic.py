#!/usr/bin/env python3
"""Smooth FLEXI/Galaexi-style DG restart data in-place while preserving HDF5 metadata.

Workflow:
1. Copy the original restart file to a new path with cp/rsync.
2. Run this script on the copied file.
3. The script overwrites only the DG_Solution dataset values and keeps all
   file/group/dataset attributes (for example NodeType) intact.

This is intended for generating a forgiving initial condition when a proper
modal filter workflow is unavailable or failing.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("h5_path", help="Path to copied .h5 file to modify in-place")
    p.add_argument("--dataset", default="DG_Solution", help="Dataset to smooth")
    p.add_argument(
        "--sigma",
        type=float,
        default=1.8,
        help="Gaussian sigma applied only on local nodal axes (default: 1.8)",
    )
    p.add_argument(
        "--batch-elements",
        type=int,
        default=20000,
        help="Number of elements to process per batch (default: 20000)",
    )
    p.add_argument(
        "--mode",
        default="nearest",
        choices=["reflect", "constant", "nearest", "mirror", "wrap"],
        help="Boundary mode passed to scipy.ndimage.gaussian_filter",
    )
    p.add_argument(
        "--clip-min",
        type=float,
        default=None,
        help="Optional lower clip bound after smoothing",
    )
    p.add_argument(
        "--clip-max",
        type=float,
        default=None,
        help="Optional upper clip bound after smoothing",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect metadata and planned operation without modifying data",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.h5_path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    with h5py.File(path, "r+" if not args.dry_run else "r") as f:
        if args.dataset not in f:
            print(f"ERROR: dataset not found: {args.dataset}", file=sys.stderr)
            return 2

        ds = f[args.dataset]
        print(f"file = {path}")
        print(f"dataset = {args.dataset}")
        print(f"shape = {ds.shape}")
        print(f"dtype = {ds.dtype}")
        print(f"chunks = {ds.chunks}")
        print(f"compression = {ds.compression}")
        print(f"file attrs = {list(f.attrs.keys())}")
        print(f"dataset attrs = {list(ds.attrs.keys())}")

        if ds.ndim != 5:
            print(
                f"ERROR: expected 5D dataset (nelem,nx,ny,nz,nvar), got {ds.ndim}D",
                file=sys.stderr,
            )
            return 3

        sigma_tuple = (0.0, args.sigma, args.sigma, args.sigma, 0.0)
        print(f"sigma = {sigma_tuple}")
        print(f"batch_elements = {args.batch_elements}")
        print(f"mode = {args.mode}")
        print(f"clip_min = {args.clip_min}")
        print(f"clip_max = {args.clip_max}")

        if args.dry_run:
            return 0

        nelem = ds.shape[0]
        nbatch = math.ceil(nelem / args.batch_elements)
        for ib in range(nbatch):
            i0 = ib * args.batch_elements
            i1 = min((ib + 1) * args.batch_elements, nelem)
            print(f"processing elements [{i0}:{i1})")
            block = ds[i0:i1, ...]
            smooth = gaussian_filter(block, sigma=sigma_tuple, mode=args.mode)

            if args.clip_min is not None or args.clip_max is not None:
                lo = -np.inf if args.clip_min is None else args.clip_min
                hi = np.inf if args.clip_max is None else args.clip_max
                smooth = np.clip(smooth, lo, hi)

            ds[i0:i1, ...] = smooth
            f.flush()

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
