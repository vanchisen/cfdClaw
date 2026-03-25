#!/usr/bin/env python3
"""Python front-end for gg_curve binary.
Runs non-interactively by piping project name to stdin.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Run gg_curve with project name")
    ap.add_argument("project", nargs="?", help="project prefix (expects <project>.grd)")
    ap.add_argument("--exe", default="./gg_curve", help="path to gg_curve executable")
    args = ap.parse_args()

    project = args.project or input("Enter project name: ").strip()
    if not project:
        raise SystemExit("project name is required")

    grd = Path(f"{project}.grd")
    if not grd.exists():
        raise SystemExit(f"Missing {grd}")

    proc = subprocess.run([args.exe], input=project + "\n", text=True)
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
