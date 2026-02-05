#!/usr/bin/env python3
"""gg_boundary.py (Python port, MVP)

Python replacement for legacy C++ `gg_boundary` in `/users/zwang197/PhaseField/Mesh/`.

What `gg_boundary` writes (per gg_boundary.C):
- <title>.rea  : boundary-condition connectivity lines only (no mesh header)
- <title>.walls: list of (eid,fid) for W boundaries
- <title>.plt  : Tecplot brick dump (mesh)

It still needs the mesh in memory in order to:
- orient elements
- build face connectivity
- map boundary faces to element faces

Usage:
  python gg_boundary.py bubble_2_fluid
  python gg_boundary.py bubble_2_fluid.grd

Outputs go to --outdir (default: cwd).

NOTE: This MVP supports HEX elements and non-periodic BCs. Periodic BCs (X/Y/Z)
raise NotImplementedError.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

# Reuse parser + geometry utilities from gg_curve.py
# Allow running as a script without installing as a package
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from phasefield_mesh_tools.gg_curve import (
    Boundary,
    BoundaryFace,
    Element,
    Vertex,
    orient_hex,
    read_grd,
    read_info,
    set_boundary_conditions,
    dump_walls,
    dump_plt,
)


def dump_boundary_rea(
    boundaries: List[Boundary],
    elements: List[Element],
    out_path: Path,
) -> None:
    """Write boundary-condition connectivity lines like gg_boundary.C Dump_rea()."""
    with out_path.open('w') as f:
        for eid, el in enumerate(elements, start=1):
            if el.etype != 2:
                raise NotImplementedError('Only HEX supported in MVP')
            for fid in range(6):
                bid = el.conn_element[fid]
                if bid >= 0:
                    # internal connectivity
                    f.write(f"E {eid} {fid+1} {bid+1} {el.conn_face[fid]+1}\n")
                else:
                    # boundary condition
                    bc_id = -bid - 1
                    bc = boundaries[bc_id]
                    btype = bc.btype

                    # zwang 11272019 symmetric boundary mapping
                    if btype in ('S', 'T', 'R'):
                        out_type = 'Z'
                    else:
                        out_type = btype

                    inline = bc.inline_params
                    if inline:
                        f.write(f"{out_type} {eid} {fid+1} {inline}\n")
                    else:
                        f.write(f"{out_type} {eid} {fid+1} 0. 0. 0.\n")

                    for ln in bc.lines:
                        # lines already include newline in .info parsing
                        f.write(ln)


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
        raise SystemExit(f"Missing {info_path}")

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

    dump_boundary_rea(boundaries, elements, outdir / f"{base.name}.rea")
    dump_walls(base.name, boundaries, bfaces, elements, outdir / f"{base.name}.walls")
    dump_plt(base.name, vertices, elements, outdir / f"{base.name}.plt")

    print(f"WROTE {outdir / (base.name + '.rea')}")


if __name__ == '__main__':
    main()
