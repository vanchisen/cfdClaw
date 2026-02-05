#!/usr/bin/env python3
"""info_template.py

Standalone Python port of the `*.info` file generation logic from:
  /users/zwang197/PhaseField/Mesh/gg_curve.C (Mesh::Read_input_files), lines ~496-582.

This writes a default `<project>.info` file with:
- ***BOUNDARY CONDITIONS*** blocks (one per boundary name line)
- *** CURVED SIDE DATA ***
- *** PERIODIC DATA ***
- *** HEAD *** (parameter header)
- *** TAIL *** (default tail)

It does NOT attempt to infer real BC types/curvature; it mirrors the C++ defaults.

Usage examples:
  python info_template.py bubble_2_fluid --boundaries "1  X_min" "2  X_max"

  # or generate from an existing .grd boundary table:
  python info_template.py bubble_2_fluid --from-grd /path/to/bubble_2_fluid.grd

Output:
  bubble_2_fluid.info
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List


def parse_grd_boundary_table(grd_path: Path) -> List[str]:
    """Return boundary name lines from a .grd file's Boundary Table section."""
    lines = grd_path.read_text(errors="ignore").splitlines()
    try:
        i = next(idx for idx, ln in enumerate(lines) if "Boundary Table" in ln)
    except StopIteration:
        raise ValueError(f"Boundary Table not found in {grd_path}")

    nbc = int(lines[i + 1].split()[0])
    out = [lines[i + 2 + k].rstrip("\n") for k in range(nbc)]
    return out


def write_info(project: str, boundaries: List[str], out_path: Path) -> None:
    """Write the default .info file exactly like gg_curve.C generates."""
    with out_path.open("w") as f:
        f.write("***BOUNDARY CONDITIONS***\n")
        for name_line in boundaries:
            f.write("+++ do NOT modify the NEXT line +++\n")
            # In C++ they write boundary_list[i]->Get_name() which already includes newline.
            # Here we ensure exactly one trailing newline.
            f.write(name_line.rstrip("\n") + "\n")
            f.write("0 CURVED\n")
            f.write("a CURVE_TYPE\n")
            f.write("W TYPE\n")
            f.write("0 LINES\n")
            f.write("\n")

        f.write("\n+++ do NOT modify the NEXT line +++\n")
        f.write("*** CURVED SIDE DATA ***\n")
        f.write("0 Number of curve types\n")
        f.write("Sphere\n")
        f.write("0.0 0.0 0.0 1.0 A\n")

        f.write("\n+++ do NOT modify the NEXT line +++\n")
        f.write("*** PERIODIC DATA ***\n")
        f.write("0.0 XPERMIN\n")
        f.write("0.0 XPERMAX\n")
        f.write("0.0 YPERMIN\n")
        f.write("0.0 YPERMAX\n")
        f.write("0.0 ZPERMIN\n")
        f.write("0.0 ZPERMAX\n")

        f.write("\n+++ do NOT modify the NEXT line +++\n")
        f.write("*** HEAD ***\n")
        f.write("15 LINES\n")
        f.write("****** PARAMETERS *****\n")
        f.write("GRIDGEN 3D -> NEKTAR\n")
        f.write("3 DIMENSIONAL RUN\n")
        f.write("9 PARAMETERS FOLLOW\n")
        f.write("0.01     KINVIS\n")
        f.write("0.72     PRANDTL\n")
        f.write("4        MODES\n")
        f.write("0.001    DT\n")
        f.write("10000    NSTEPS\n")
        f.write("1        EQTYPE\n")
        f.write("2        INTYPE\n")
        f.write("1000     IOSTEP\n")
        f.write("10       HISSTEP\n")
        f.write("0  Lines of passive scalar data follows\n")
        f.write("0  LOGICAL SWITCHES FOLLOW\n")
        f.write("Dummy line from old nekton file\n")

        f.write("\n+++ do NOT modify the NEXT line +++\n")
        f.write("*** TAIL ***\n")
        f.write("16 LINES\n")
        f.write("***** NO THERMAL BOUNDARY CONDITIONS *****\n")
        f.write("4 INITIAL CONDITIONS *****\n")
        f.write("Given\n")
        f.write("u = 1.0\n")
        f.write("v = 0.0\n")
        f.write("w = 0.0\n")
        f.write("***** DRIVE FORCE DATA ***** PRESSURE GRAD, FLOW, Q\n")
        f.write("0 Lines of Drive force data follow\n")
        f.write("***** Variable Property Data ***** Overrrides Parameter data.\n")
        f.write("1 Lines follow.\n")
        f.write("0 PACKETS OF DATA FOLLOW\n")
        f.write("***** HISTORY AND INTEGRAL DATA *****\n")
        f.write("0 POINTS.  Hcode, I,J,H,IEL\n")
        f.write("UVWP  H  1 0 0 10\n")
        f.write("***** OUTPUT FIELD SPECIFICATION *****\n")
        f.write("0 SPECIFICATIONS FOLLOW\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="Base project name (e.g. bubble_2_fluid)")

    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-grd", type=Path, help="Read Boundary Table from this .grd")
    src.add_argument("--boundaries", nargs="+", help="Boundary name lines (e.g. '1  X_min')")

    ap.add_argument("-o", "--output", type=Path, help="Output .info path (default: <project>.info)")
    args = ap.parse_args()

    if args.from_grd:
        boundaries = parse_grd_boundary_table(args.from_grd)
    else:
        boundaries = [b for b in (args.boundaries or [])]

    out = args.output if args.output else Path(f"{args.project}.info")
    write_info(args.project, boundaries, out)
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
