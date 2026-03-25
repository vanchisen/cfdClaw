#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from gg_common_pure import parse_grd


def main() -> int:
    ap = argparse.ArgumentParser(description="Pure Python gg_curve replacement")
    ap.add_argument("project")
    ap.add_argument("--scale", nargs=3, type=float, default=[1.0, 1.0, 1.0])
    ap.add_argument("--output", default=None, help="default: <project>.rea")
    args = ap.parse_args()

    project = args.project
    grd = Path(f"{project}.grd")
    out = Path(args.output or f"{project}.rea")

    mesh = parse_grd(grd, tuple(args.scale))
    mesh.orient_elements()
    mesh.connect()

    num_elmts = len(mesh.elements)
    num_fluid = sum(1 for g in mesh.groups if g == 1)

    with out.open("w") as f:
        f.write("**MESH DATA** x,y,z, values of vertices 1,2,3,4.\n")
        f.write(f"{num_elmts}  {num_fluid}\t 3\t1   NEL NDIM NLEVEL\n")
        for eid, e in enumerate(mesh.elements, 1):
            if e.etype == 0:
                gid = mesh.groups[eid - 1] - 1
                f.write(f"Element {eid} Hex  Group {gid} \n")
            elif e.etype == 1:
                f.write(f"Element {eid} Tet\n")
            elif e.etype == 2:
                f.write(f"Element {eid} Prism\n")
            else:
                f.write(f"Element {eid} Pyr\n")
            f.write(" ".join(f"{mesh.vertices[v].x:.6f}" for v in e.vert_ids) + " \n")
            f.write(" ".join(f"{mesh.vertices[v].y:.6f}" for v in e.vert_ids) + " \n")
            f.write(" ".join(f"{mesh.vertices[v].z:.6f}" for v in e.vert_ids) + " \n")

        f.write("***** CURVED SIDE DATA ***** \n")
        f.write("0 Number of curve types\n")
        f.write("0 Curved sides follow\n")
        f.write("***** BOUNDARY CONDITIONS ***** \n")
        f.write("***** FLUID BOUNDARY CONDITIONS ***** \n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
