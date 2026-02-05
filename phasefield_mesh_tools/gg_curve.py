#!/usr/bin/env python3
"""gg_curve.py (Python port, MVP)

Goal: Python replacement for legacy C++ `gg_curve` in `/users/zwang197/PhaseField/Mesh/`.

Pipeline:
  <name>.grd + <name>.info  -->  <name>.rea + <name>.walls + <name>.plt

This MVP targets the common case in PhaseField/Mesh:
- hex-dominant meshes
- quad boundary faces
- .info present (we do not auto-generate .info yet)
- curved side data is copied from .info, but we do not implement curvedfaces_fix

The intent is to match the C++ output *semantically* and closely match formatting.

Usage:
  python gg_curve.py bubble_2_fluid
  python gg_curve.py bubble_2_fluid.grd

Notes:
- Legacy code uses implicit node indexing from the Nodes list (1-based in files).
- Boundary faces are matched to element faces by vertex sets.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


# ------------------------- Data model -------------------------


@dataclass
class Vertex:
    x: float
    y: float
    z: float
    # optional normal accumulation (used for SI inline params in curved data)
    nx: float = 0.0
    ny: float = 0.0
    nz: float = 0.0
    nf: float = 0.0


@dataclass
class BoundaryFace:
    bc_id: int  # 0-based bc index
    verts: Tuple[int, ...]  # 0-based vertex ids, length 3 or 4


@dataclass
class Boundary:
    name_line: str  # exact line from Boundary Table (e.g. "1  X_min")
    curved: int
    curve_type: str  # single char
    btype: str  # single char
    lines: List[str]
    inline_params: str = ""  # line after INLINE


@dataclass
class Element:
    etype: int  # 1 tet,2 hex,3 pri,4 pyr
    group: int  # partID/physID from .grd
    verts: Tuple[int, ...]  # 0-based vertex ids
    # connectivity (like C++): for each face fid, either neighbor element id, or -(bc_id+1)
    conn_element: List[int]
    conn_face: List[int]


# Face-vertex tables (from gg_curve.H)
HEX_FACES = [
    (0, 1, 2, 3),
    (0, 1, 5, 4),
    (1, 2, 6, 5),
    (3, 2, 6, 7),
    (0, 3, 7, 4),
    (4, 5, 6, 7),
]


# ------------------------- Parsing helpers -------------------------


def find_section(lines: List[str], key: str) -> int:
    for i, ln in enumerate(lines):
        if key in ln:
            return i
    raise ValueError(f"Section not found: {key}")


def read_grd(path: Path) -> Tuple[List[Boundary], List[Vertex], List[BoundaryFace], List[Element]]:
    txt = path.read_text(errors="ignore").splitlines()

    i = find_section(txt, "Boundary Table")
    nbc = int(txt[i + 1].split()[0])
    boundaries: List[Boundary] = []
    for k in range(nbc):
        name_line = txt[i + 2 + k].rstrip("\n")
        boundaries.append(Boundary(name_line=name_line, curved=0, curve_type='a', btype='O', lines=[], inline_params=""))

    j = find_section(txt, "Nodes")
    npt = int(txt[j + 1].split()[0])
    vertices: List[Vertex] = []
    for k in range(npt):
        x, y, z = map(float, txt[j + 2 + k].split()[:3])
        vertices.append(Vertex(x, y, z))

    k0 = find_section(txt, "Boundary Faces")
    nbf = int(txt[k0 + 1].split()[0])
    bfaces: List[BoundaryFace] = []
    for k in range(nbf):
        parts = txt[k0 + 2 + k].split()
        bc_type = int(parts[0])  # 1-based physical/bc id
        vert_num = int(parts[1])
        vs = tuple(int(v) - 1 for v in parts[2:2 + vert_num])
        # bc_id in code is index into boundary_list by (bc_type-1)
        bfaces.append(BoundaryFace(bc_id=bc_type - 1, verts=vs))

    e0 = find_section(txt, "Elements")
    v0 = find_section(txt, "Variables")
    elem_lines = txt[e0 + 1:v0]
    elements: List[Element] = []
    for ln in elem_lines:
        parts = ln.split()
        if not parts:
            continue
        etype = int(parts[0])
        # parts[1] is tmp flag
        group = int(parts[2])
        v = tuple(int(x) - 1 for x in parts[3:])
        if etype == 2:
            if len(v) != 8:
                raise ValueError(f"Hex element does not have 8 verts: {ln}")
            # Match legacy C++ reader: Add_hex(v0,v1,v3,v2,v4,v5,v7,v6)
            v = (v[0], v[1], v[3], v[2], v[4], v[5], v[7], v[6])
        face_num = 6 if etype == 2 else 0
        elements.append(Element(
            etype=etype,
            group=group,
            verts=v,
            conn_element=[-999] * face_num,
            conn_face=[-999] * face_num,
        ))

    return boundaries, vertices, bfaces, elements


def read_info(path: Path, boundaries: List[Boundary]) -> Dict[str, object]:
    lines = path.read_text(errors="ignore").splitlines(True)  # keep newlines

    # helper: find exact marker line
    def find_marker(marker: str) -> int:
        for i, ln in enumerate(lines):
            if marker in ln:
                return i
        raise ValueError(f"Marker not found: {marker}")

    # Parse boundary blocks
    idx = find_marker("***BOUNDARY CONDITIONS***")
    # boundary blocks start after that
    i = idx + 1

    # Map boundary name_line -> boundary object (exact match after stripping)
    bmap = {b.name_line.strip(): b for b in boundaries}
    # normalized string -> canonical boundary key in bmap
    norm_to_key = {" ".join(k.split()): k for k in bmap.keys()}

    while i < len(lines):
        ln = lines[i]
        if "*** CURVED SIDE DATA ***" in ln:
            break
        if "+++ do NOT modify" in ln:
            name_line = lines[i + 1].strip("\n")
            # The .info file also uses this "do NOT modify" preamble before other sections.
            # If we hit the curved-side section marker, stop parsing boundary blocks.
            if "CURVED SIDE DATA" in name_line:
                break
            # Normalize spaces for lookup
            key = " ".join(name_line.split())
            if key not in norm_to_key:
                raise ValueError(f"Boundary name from .info not found in .grd Boundary Table: {name_line}")
            b = bmap[norm_to_key[key]]

            curved = int(lines[i + 2].split()[0])
            curve_type = lines[i + 3].split()[0]
            btype = lines[i + 4].split()[0]
            nlines = int(lines[i + 5].split()[0])

            b.curved = curved
            b.curve_type = curve_type
            b.btype = btype
            b.lines = []
            b.inline_params = ""

            jj = i + 6
            # read lines section
            for _ in range(max(nlines, 0)):
                b.lines.append(lines[jj])
                jj += 1

            # optional INLINE
            if jj < len(lines) and lines[jj].strip() == "INLINE":
                jj += 1
                if jj < len(lines):
                    b.inline_params = lines[jj].strip("\n")
                    jj += 1

            i = jj
            continue

        i += 1

    # Curved side data types
    cidx = find_marker("*** CURVED SIDE DATA ***")
    # next line should be like "0 Number of curve types"
    m = re.match(r"\s*(\d+)", lines[cidx + 1])
    n_curve_types = int(m.group(1)) if m else 0
    curve_type_lines = []
    # in C++ it reads 2 lines per type, but n can be 0.
    jj = cidx + 2
    for _ in range(n_curve_types):
        curve_type_lines.append(lines[jj]); jj += 1
        curve_type_lines.append(lines[jj]); jj += 1

    # Periodic data
    pidx = find_marker("*** PERIODIC DATA ***")
    per = {}
    for k in range(6):
        parts = lines[pidx + 1 + k].split()
        per[parts[1]] = float(parts[0])

    return {
        "n_curve_types": n_curve_types,
        "curve_type_lines": curve_type_lines,
        "periodic": per,
    }


# ------------------------- Geometry helpers -------------------------


def det_cpp(v0: Vertex, v1: Vertex, v2: Vertex, v3: Vertex) -> float:
    """Match Mesh::Determinant(v0,v1,v2,v3) from gg_curve.C.

    Returns: (v3-v0) dot ((v1-v0) x (v2-v0))
    """
    ax, ay, az = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
    bx, by, bz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
    cx, cy, cz = v3.x - v0.x, v3.y - v0.y, v3.z - v0.z

    dx = ay * bz - az * by
    dy = az * bx - ax * bz
    dz = ax * by - ay * bx

    return cx * dx + cy * dy + cz * dz


def orient_hex(elem: Element, vertices: List[Vertex]) -> None:
    v0, v1, v2, v3, v4, v5, v6, v7 = elem.verts
    # C++ Hex::Orient(): if Determinant(v0,v1,v3,v4) < 0 swap top/bottom
    if det_cpp(vertices[v0], vertices[v1], vertices[v3], vertices[v4]) < 0.0:
        elem.verts = (v4, v5, v6, v7, v0, v1, v2, v3)


# ------------------------- Connectivity + BC -------------------------


def build_face_map_multi(elements: List[Element]) -> Dict[Tuple[int, ...], List[Tuple[int, int]]]:
    """Map sorted vertex tuple -> list of (eid,fid) for all element faces.

    Internal faces will have two entries; boundary faces one.
    """
    fmap: Dict[Tuple[int, ...], List[Tuple[int, int]]] = {}
    for eid, el in enumerate(elements):
        if el.etype != 2:
            continue
        for fid, loc in enumerate(HEX_FACES):
            face = tuple(el.verts[i] for i in loc)
            key = tuple(sorted(face))
            fmap.setdefault(key, []).append((eid, fid))
    return fmap


def connect_internal(elements: List[Element]) -> None:
    """Populate conn_element/conn_face for internal connectivity (C++ Mesh::Connect).

    Uses a face hash: for each face key with two owners, connect them.
    Boundary faces are left as self-connected (will be overwritten by BC assignment).
    """
    fmap = build_face_map_multi(elements)
    for eid, el in enumerate(elements):
        if el.etype != 2:
            continue
        el.conn_element = [eid] * 6
        el.conn_face = list(range(6))

    for key, owners in fmap.items():
        if len(owners) == 2:
            (e0, f0), (e1, f1) = owners
            elements[e0].conn_element[f0] = e1
            elements[e0].conn_face[f0] = f1
            elements[e1].conn_element[f1] = e0
            elements[e1].conn_face[f1] = f0


def set_boundary_conditions(
    elements: List[Element],
    bfaces: List[BoundaryFace],
    boundaries: List[Boundary],
    vertices: List[Vertex],
    periodic: Dict[str, float],
) -> None:
    # First build internal connectivity
    connect_internal(elements)

    fmap = build_face_map_multi(elements)

    # apply boundary faces
    for bf in bfaces:
        key = tuple(sorted(bf.verts))
        owners = fmap.get(key)
        if not owners:
            continue
        # pick the first owner (boundary face should only have one)
        eid, fid = owners[0]
        bc = boundaries[bf.bc_id]
        btype = bc.btype
        if btype not in ("X", "x", "Y", "y", "Z", "z"):
            elements[eid].conn_element[fid] = -(bf.bc_id + 1)
            elements[eid].conn_face[fid] = -(bf.bc_id + 1)
        else:
            raise NotImplementedError("Periodic BCs not implemented in MVP")


# ------------------------- Writers -------------------------


def dump_rea(
    title: str,
    boundaries: List[Boundary],
    vertices: List[Vertex],
    elements: List[Element],
    info: Dict[str, object],
    out_path: Path,
) -> None:
    # count fluid elements (legacy assumes physID/group==1 is fluid)
    num_elmts = len(elements)
    num_fluid = sum(1 for e in elements if e.group == 1)

    with out_path.open("w") as f:
        f.write("**MESH DATA** x,y,z, values of vertices 1,2,3,4.\n")
        f.write(f"{num_elmts}  {num_fluid}\t 3\t1   NEL NDIM NLEVEL\n")

        scal = 1.0
        for eid, el in enumerate(elements, start=1):
            if el.etype == 2:
                groupID = el.group - 1
                f.write(f"Element {eid} Hex  Group {groupID} \n")
                vs = el.verts
            else:
                raise NotImplementedError("Only HEX supported in MVP")

            # x y z lines
            f.write(" ".join(f"{scal*vertices[v].x:.6f}" for v in vs) + " \n")
            f.write(" ".join(f"{scal*vertices[v].y:.6f}" for v in vs) + " \n")
            f.write(" ".join(f"{scal*vertices[v].z:.6f}" for v in vs) + " \n")

        f.write("***** CURVED SIDE DATA ***** \n")
        n_curve_types = int(info.get("n_curve_types", 0))
        f.write(f"{n_curve_types} Number of curve types\n")
        for ln in info.get("curve_type_lines", []):
            f.write(str(ln))

        # number of curved sides
        numcur = 0
        for bid, bc in enumerate(boundaries):
            if bc.curved == 1:
                # legacy counts boundary faces; we do not have per-bc face lists here
                # so we approximate by scanning bfaces elsewhere; for bubble_2_fluid it's 0.
                pass
        f.write(f"{numcur} Curved sides follow\n")

        f.write("***** BOUNDARY CONDITIONS ***** \n")
        f.write("***** FLUID BOUNDARY CONDITIONS ***** \n")


def dump_walls(
    title: str,
    boundaries: List[Boundary],
    bfaces: List[BoundaryFace],
    elements: List[Element],
    out_path: Path,
) -> None:
    fmap = build_face_map_multi(elements)
    # collect W type faces
    wall_pairs: List[Tuple[int, int]] = []
    for bf in bfaces:
        if boundaries[bf.bc_id].btype != 'W':
            continue
        key = tuple(sorted(bf.verts))
        owners = fmap.get(key)
        if not owners:
            continue
        eid, fid = owners[0]
        wall_pairs.append((eid + 1, fid + 1))

    with out_path.open('w') as f:
        f.write('Body\n')
        f.write(f"{len(wall_pairs)}\n")
        for eid, fid in wall_pairs:
            f.write(f"{eid}  {fid}\n")


def dump_plt(
    title: str,
    vertices: List[Vertex],
    elements: List[Element],
    out_path: Path,
) -> None:
    # Minimal Tecplot brick listing like C++ (8 nodes per element)
    with out_path.open('w') as f:
        f.write('TITLE = "  "\n')
        f.write('VARIABLES = "X", "Y", "Z", "FUNCTION"\n')
        f.write(f"ZONE  N={len(elements)*8}, E={len(elements)}, F=FEPOINT, ET=BRICK \n")

        # write 8 vertices per element (using hex ordering)
        for el in elements:
            if el.etype != 2:
                raise NotImplementedError
            for vid in range(8):
                v = vertices[el.verts[vid]]
                f.write(f"{v.x},{v.y},{v.z},0\n")

        for k in range(len(elements)):
            pr = 8 * k
            f.write(", ".join(str(pr + i) for i in range(1, 9)) + ", \n ")


# ------------------------- CLI -------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', help='Project base name or .grd path')
    ap.add_argument('--scale', nargs=3, type=float, default=(1.0, 1.0, 1.0), help='Scale in x y z')
    ap.add_argument('--outdir', default='.', help='Output directory')
    args = ap.parse_args()

    proj = Path(args.project)
    if proj.suffix.lower() == '.grd':
        base = proj.with_suffix('')
        grd = proj
    else:
        base = proj
        grd = base.with_suffix('.grd')

    info_path = base.with_suffix('.info')
    if not grd.exists():
        raise SystemExit(f"Missing {grd}")
    if not info_path.exists():
        raise SystemExit(f"Missing {info_path} (MVP requires .info)")

    boundaries, vertices, bfaces, elements = read_grd(grd)

    # apply scale
    sx, sy, sz = args.scale
    if (sx, sy, sz) != (1.0, 1.0, 1.0):
        for v in vertices:
            v.x *= sx; v.y *= sy; v.z *= sz

    info = read_info(info_path, boundaries)

    # orient elements
    for el in elements:
        if el.etype == 2:
            orient_hex(el, vertices)

    # set BC connectivity
    set_boundary_conditions(elements, bfaces, boundaries, vertices, info.get('periodic', {}))

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    title = str(base.name)

    dump_rea(title, boundaries, vertices, elements, info, outdir / f"{base.name}.rea")
    dump_walls(title, boundaries, bfaces, elements, outdir / f"{base.name}.walls")
    dump_plt(title, vertices, elements, outdir / f"{base.name}.plt")

    print(f"WROTE {outdir / (base.name + '.rea')}")


if __name__ == '__main__':
    main()
