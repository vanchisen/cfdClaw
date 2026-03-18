#!/usr/bin/env python3
from paraview.simple import *
import os
import sys

if len(sys.argv) != 3:
    raise SystemExit('Usage: pvpython toyota_midz_to_vtk.py <case_dir> <out_vtk>')

case_dir = sys.argv[1]
out_vtk = sys.argv[2]
nek = os.path.join(case_dir, 'avgcyl.nek5000')

src = OpenDataFile(nek)
if src is None:
    raise RuntimeError(f'Cannot open {nek}')

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()

# Jump to latest timestep if available
try:
    tvals = scene.TimeKeeper.TimestepValues
    if tvals and len(tvals) > 0:
        scene.AnimationTime = tvals[-1]
except Exception:
    pass

UpdatePipeline(proxy=src)
b = src.GetDataInformation().GetBounds()
zmid = 0.5 * (b[4] + b[5])

sl = Slice(Input=src)
sl.SliceType = 'Plane'
sl.SliceType.Origin = [0.5 * (b[0] + b[1]), 0.5 * (b[2] + b[3]), zmid]
sl.SliceType.Normal = [0.0, 0.0, 1.0]

UpdatePipeline(proxy=sl)
SaveData(out_vtk, proxy=sl)

print(f'Wrote {out_vtk}')
print(f'Bounds={b}, zmid={zmid}')
