#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from gg_common_pure import parse_grd, parse_info


def main() -> int:
    ap = argparse.ArgumentParser(description="Pure Python gg_boundary replacement")
    ap.add_argument("project")
    ap.add_argument("--info", default=None, help="default: <project>.info")
    ap.add_argument("--output", default=None, help="default: <project>.rea")
    ap.add_argument("--scale", nargs=3, type=float, default=[1.0, 1.0, 1.0])
    args = ap.parse_args()

    project = args.project
    grd = Path(f"{project}.grd")
    info = Path(args.info or f"{project}.info")
    out = Path(args.output or f"{project}.rea")

    mesh = parse_grd(grd, tuple(args.scale))
    parse_info(info, mesh.boundaries)
    mesh.orient_elements()
    mesh.connect()
    mesh.set_boundary_conditions()

    with out.open("w") as f:
        for eid, e in enumerate(mesh.elements, 1):
            for fid, ce in enumerate(e.conn_element, 1):
                if ce >= 0:
                    f.write(f"E {eid} {fid} {ce + 1} {e.conn_face[fid - 1] + 1}\n")
                else:
                    bid = -ce - 1
                    bc = mesh.boundaries[bid]
                    btype = "Z" if bc.btype in ("S", "T", "R") else bc.btype
                    f.write(f"{btype} {eid} {fid} {bc.inline_params}")
                    for ln in bc.lines:
                        f.write(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
