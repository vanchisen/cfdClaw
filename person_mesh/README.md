# Person outline → Gmsh mesh (2D)

Inputs:
- `Jiachuan.jpg`

Script:
- `extract_outline.py`

Outputs (default run):
- `out/outline_overlay.png` — diagnostic overlay (photo + extracted outline)
- `out/outline_pixels.csv` — outline polyline in pixel coordinates
- `out/person_channel.geo` — Gmsh geometry: rectangular channel with the silhouette cut out
- `out/person_channel.msh` — Gmsh 2D mesh (msh2)

Typical run:
```bash
cd /users/zwang197/.openclaw/workspace/person_mesh
python3 extract_outline.py Jiachuan.jpg --outdir out \
  --downsample 4 --simplify 3.0 --vmax-snow 0.80 --smin-color 0.16
```

Notes:
- Geometry is normalized so the silhouette height is `H=1.0` (change with `--H`).
- Domain extents are controlled by `--upstream/--downstream/--domain-W` in multiples of `H`.
- If the extracted component picks bushes/background, tighten thresholds or adjust ROI/target.
