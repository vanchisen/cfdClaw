#!/usr/bin/env python3
"""
Python version of gmsh2grd.cc (focused on this MURI hex workflow).
Converts <project>.msh -> <project>.grd.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def read_msh_sections(text: str):
    lines = text.splitlines()
    i = 0
    sections = {}
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("$") and not line.startswith("$End"):
            name = line[1:]
            end = f"$End{name}"
            i += 1
            block = []
            while i < len(lines) and lines[i].strip() != end:
                block.append(lines[i])
                i += 1
            sections[name] = block
        i += 1
    return sections


def parse_physical_names(block):
    if not block:
        return {}
    n = int(block[0].strip())
    out = {}
    for row in block[1:1 + n]:
        row = row.strip()
        if not row:
            continue
        parts = row.split(maxsplit=2)
        if len(parts) < 3:
            continue
        dim = int(parts[0])
        pid = int(parts[1])
        name = parts[2].strip().strip('"')
        if dim == 2:
            out[pid] = name
    return out


def parse_nodes(block):
    n = int(block[0].strip())
    nodes = {}
    for row in block[1:1 + n]:
        parts = row.split()
        nid = int(parts[0])
        nodes[nid] = (float(parts[1]), float(parts[2]), float(parts[3]))
    return nodes


def parse_elements(block):
    n = int(block[0].strip())
    bfaces = []  # (physID, [v0,v1,v2,v3]) from gmsh quad type=3
    hexes = []   # (physID, [8 node ids]) from gmsh hex type=5
    for row in block[1:1 + n]:
        p = row.split()
        eid = int(p[0])
        etype = int(p[1])
        ntags = int(p[2])
        tags = [int(x) for x in p[3:3 + ntags]]
        conn = [int(x) for x in p[3 + ntags:]]
        phys = tags[0] if tags else 0

        if etype == 3 and len(conn) == 4:  # quad face
            bfaces.append((phys, conn))
        elif etype == 5 and len(conn) == 8:  # hex
            hexes.append((phys, conn))
        else:
            # ignored in this workflow
            pass
    return bfaces, hexes


def write_grd(out_path: Path, physical_2d, nodes, bfaces, hexes):
    with out_path.open("w") as f:
        # Boundary table
        f.write("Boundary Table \n")
        bc_ids = sorted({pid for pid, _ in bfaces if pid in physical_2d})
        f.write(f"{len(bc_ids)}\n")
        for pid in bc_ids:
            f.write(f"{pid}  {physical_2d[pid]}\n")

        # Nodes
        f.write("Nodes\n")
        f.write(f"{len(nodes)}\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{x:<20.15g}  {y:<20.15g}  {z:<20.15g}\n")

        # Boundary faces
        f.write("Boundary Faces \n")
        f.write(f"{len(bfaces)}\n")
        for phys, (v0, v1, v2, v3) in bfaces:
            f.write(f"{phys}  4  {v0}  {v1}  {v2}  {v3}\n")

        # Elements (keep same node reorder as C++ tool)
        f.write("Elements\n")
        for phys, conn in hexes:
            v0, v1, v2, v3, v4, v5, v6, v7 = conn
            f.write(f"2 1  {phys}  {v0}  {v1}  {v3}  {v2}  {v4}  {v5}  {v7}  {v6}\n")

        f.write("Variables\n")


def main():
    ap = argparse.ArgumentParser(description="Convert gmsh .msh to .grd (Python version)")
    ap.add_argument("project", nargs="?", help="project name without extension (e.g., muri_fluid)")
    ap.add_argument("--msh", help="explicit path to .msh")
    ap.add_argument("--grd", help="explicit output .grd path")
    args = ap.parse_args()

    if not args.project and not args.msh:
        args.project = input("Please input the name of gmsh file... ").strip()

    msh = Path(args.msh) if args.msh else Path(f"{args.project}.msh")
    grd = Path(args.grd) if args.grd else Path(f"{args.project}.grd")

    text = msh.read_text()
    sections = read_msh_sections(text)

    if "PhysicalNames" not in sections:
        raise SystemExit("PhysicalNames not found in *.msh")

    physical_2d = parse_physical_names(sections.get("PhysicalNames", []))
    nodes = parse_nodes(sections["Nodes"])
    bfaces, hexes = parse_elements(sections["Elements"])

    print(f"Number of BC: {len(sorted({pid for pid, _ in bfaces if pid in physical_2d}))}")
    print(f"Nmber of vertices        {len(nodes)}")
    print(f"Number of Boundary Faces {len(bfaces)}")
    print(f"Number of Elements       {len(hexes)}")
    print(f"Number of fluid elements {sum(1 for phys,_ in hexes if phys == 1)}")

    write_grd(grd, physical_2d, nodes, bfaces, hexes)
    print(f"Wrote {grd}")


if __name__ == "__main__":
    main()
