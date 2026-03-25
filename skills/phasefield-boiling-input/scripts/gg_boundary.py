#!/usr/bin/env python3
"""Python front-end for gg_boundary binary.
Runs non-interactively by piping project name to stdin.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Run gg_boundary with project name")
    ap.add_argument("project", nargs="?", help="project prefix (expects <project>.grd and <project>.info)")
    ap.add_argument("--exe", default="./gg_boundary", help="path to gg_boundary executable")
    args = ap.parse_args()

    project = args.project or input("Enter project name: ").strip()
    if not project:
        raise SystemExit("project name is required")

    grd = Path(f"{project}.grd")
    info = Path(f"{project}.info")
    if not grd.exists():
        raise SystemExit(f"Missing {grd}")
    if not info.exists():
        raise SystemExit(f"Missing {info}")

    proc = subprocess.run([args.exe], input=project + "\n", text=True)
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
