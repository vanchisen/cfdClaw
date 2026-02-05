#!/usr/bin/env python3
"""gmsh2grd.py

Python replacement for /users/zwang197/PhaseField/Mesh/gmsh2grd.cc.

Converts a Gmsh .msh file to the custom .grd format consumed by gg_curve/gg_boundary.

This implementation uses meshio to robustly read Gmsh meshes, but it *emulates* the
legacy output semantics:
- Boundary Table: from 2D PhysicalNames (surface groups)
- Nodes: coordinates in the same order as meshio provides (we map node IDs accordingly)
- Boundary Faces: quad faces (and optionally tris) tagged with a physical id
- Elements: hex8 elements tagged with a physical id

Notes / compatibility:
- Legacy C++ assumed boundary quads appear first in $Elements; we do not.
- Legacy C++ writes nodes without IDs; vertex indices in faces/elements are 1-based
  w.r.t. the written Nodes list.

Usage:
  python gmsh2grd.py bubble_2_fluid.msh
  python gmsh2grd.py bubble_2_fluid   # will try .msh suffix

Outputs:
  bubble_2_fluid.grd
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import meshio


def _read_mesh(path: Path) -> meshio.Mesh:
    return meshio.read(path)


def _extract_surface_physnames(mesh: meshio.Mesh) -> List[Tuple[int, str]]:
    """Return list of (phys_id, name) for 2D physical groups.

    meshio stores gmsh physical names in mesh.field_data: {name: [id, dim]}
    """
    out: List[Tuple[int, str]] = []
    field_data = getattr(mesh, "field_data", {}) or {}
    for name, arr in field_data.items():
        # arr is typically [id, dim]
        if len(arr) >= 2:
            phys_id = int(arr[0])
            dim = int(arr[1])
            if dim == 2:
                out.append((phys_id, name))
    out.sort(key=lambda x: x[0])
    return out


def _node_map(mesh: meshio.Mesh) -> Tuple[np.ndarray, Dict[int, int]]:
    """Return points array and map from mesh node index -> 1-based .grd index."""
    pts = np.asarray(mesh.points, dtype=float)
    # meshio already provides points in a consistent ordering; use that.
    # map: mesh node index -> grd node id (1-based)
    m = {i: i + 1 for i in range(pts.shape[0])}
    return pts, m


def _get_cell_data(mesh: meshio.Mesh, key: str, default=None):
    cd = getattr(mesh, "cell_data_dict", None)
    if cd is None:
        # older meshio
        cd = {}
    return cd.get(key, default)


def _collect_boundary_faces(mesh: meshio.Mesh) -> List[Tuple[int, int, List[int]]]:
    """Collect boundary faces as (phys_id, vert_num, [v...]) with v 1-based.

    We include quads and triangles if present.

    We use gmsh:physical tags when present. meshio stores these in cell_data under
    'gmsh:physical' for each cell block.
    """
    faces: List[Tuple[int, int, List[int]]] = []

    phys_by_block = _get_cell_data(mesh, "gmsh:physical", {})

    for block_idx, cell_block in enumerate(mesh.cells):
        ctype = cell_block.type
        if ctype not in ("quad", "triangle"):
            continue
        data = np.asarray(cell_block.data, dtype=int)

        phys_tags = None
        if isinstance(phys_by_block, dict):
            # meshio 5+: cell_data_dict maps name -> {cell_type: array}
            phys_tags = phys_by_block.get(ctype)
        else:
            # fallback
            phys_tags = None

        if phys_tags is None:
            # Try cell_data (list aligned with mesh.cells)
            if hasattr(mesh, "cell_data") and isinstance(mesh.cell_data, dict):
                # mesh.cell_data[name] is list aligned with mesh.cells
                tags_list = mesh.cell_data.get("gmsh:physical")
                if tags_list is not None and len(tags_list) > block_idx:
                    phys_tags = tags_list[block_idx]

        if phys_tags is None:
            # No physical tags; skip because legacy pipeline depends on BC ids.
            continue

        phys_tags = np.asarray(phys_tags, dtype=int)
        if phys_tags.shape[0] != data.shape[0]:
            raise ValueError(f"Physical tag count mismatch for {ctype}")

        for conn, pid in zip(data, phys_tags):
            pid = int(pid)
            verts = [int(v) + 1 for v in conn.tolist()]  # 1-based
            faces.append((pid, len(verts), verts))

    return faces


def _collect_hex_elements(mesh: meshio.Mesh) -> List[Tuple[int, int, List[int]]]:
    """Collect hex elements as (etype, phys_id, [v...]) with v 1-based.

    Legacy .grd uses:
      Ntmp1 Ntmp2 partID v0 v1 v2 v3 v4 v5 v6 v7
    where Ntmp1=2 for hex. We will set Ntmp2=1 (as in legacy) and partID=phys_id.

    Vertex ordering: legacy C++ writer gmsh2grd writes (v0 v1 v3 v2 v4 v5 v7 v6).
    That is, it swaps v2<->v3 and v6<->v7 relative to gmsh ordering.

    meshio gives hex connectivity in gmsh ordering; we apply the same swap pattern.
    """
    elems: List[Tuple[int, int, List[int]]] = []

    phys_by_block = _get_cell_data(mesh, "gmsh:physical", {})

    for block_idx, cell_block in enumerate(mesh.cells):
        if cell_block.type != "hexahedron":
            continue
        data = np.asarray(cell_block.data, dtype=int)

        phys_tags = None
        if isinstance(phys_by_block, dict):
            phys_tags = phys_by_block.get("hexahedron")
        else:
            phys_tags = None

        if phys_tags is None:
            if hasattr(mesh, "cell_data") and isinstance(mesh.cell_data, dict):
                tags_list = mesh.cell_data.get("gmsh:physical")
                if tags_list is not None and len(tags_list) > block_idx:
                    phys_tags = tags_list[block_idx]

        if phys_tags is None:
            # If missing, default phys id 1
            phys_tags = np.ones((data.shape[0],), dtype=int)

        phys_tags = np.asarray(phys_tags, dtype=int)
        if phys_tags.shape[0] != data.shape[0]:
            raise ValueError("Physical tag count mismatch for hexahedron")

        for conn, pid in zip(data, phys_tags):
            pid = int(pid)
            v = [int(x) + 1 for x in conn.tolist()]  # 1-based
            # apply swap pattern: 0,1,3,2,4,5,7,6
            v = [v[0], v[1], v[3], v[2], v[4], v[5], v[7], v[6]]
            elems.append((2, pid, v))

    return elems


def write_grd(
    msh_path: Path,
    grd_path: Path,
) -> None:
    mesh = _read_mesh(msh_path)

    # boundary table
    bc = _extract_surface_physnames(mesh)
    if not bc:
        raise SystemExit("No 2D PhysicalNames found (need surface BC names in .msh)")

    pts, _ = _node_map(mesh)

    faces = _collect_boundary_faces(mesh)
    # Keep only faces whose phys_id appears in the 2D physical name list.
    bc_ids = {pid for pid, _ in bc}
    faces = [f for f in faces if f[0] in bc_ids]

    elems = _collect_hex_elements(mesh)

    with grd_path.open("w") as f:
        f.write("Boundary Table \n")
        f.write(f"{len(bc)}\n")
        for pid, name in bc:
            f.write(f"{pid}  {name}\n")

        f.write("Nodes\n")
        f.write(f"{pts.shape[0]}\n")
        # match legacy formatting loosely: three columns, left aligned
        for x, y, z in pts:
            f.write(f"{x:<20.15g}  {y:<20.15g}  {z:<20.15g}\n")

        f.write("Boundary Faces \n")
        f.write(f"{len(faces)}\n")
        # legacy writes: physID  grd_face_type(=4)  v0 v1 v2 v3
        # For triangles, write vert_num=3 and omit v3.
        for phys_id, nvert, verts in faces:
            # In gg_curve, it expects: BC_type vert_num v0 v1 v2 (v3)
            f.write(f"{phys_id}  {nvert}  " + "  ".join(str(v) for v in verts) + "\n")

        f.write("Elements\n")
        # legacy writes: element_type tmp physID v0..v7
        # tmp is 1, and physID is written as partID.
        for etype, pid, verts in elems:
            f.write(f"{etype}  1  {pid}  " + "  ".join(str(v) for v in verts) + "\n")

        f.write("Variables\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Input Gmsh .msh file or base name")
    ap.add_argument("-o", "--output", help="Output .grd path (default: input base + .grd)")
    args = ap.parse_args()

    inp = Path(args.input)
    if inp.suffix == "":
        msh = inp.with_suffix(".msh")
        base = inp
    elif inp.suffix.lower() == ".msh":
        msh = inp
        base = inp.with_suffix("")
    else:
        raise SystemExit("Input must be a .msh file or base name")

    if not msh.exists():
        raise SystemExit(f"Missing input: {msh}")

    out = Path(args.output) if args.output else base.with_suffix(".grd")
    write_grd(msh, out)
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
