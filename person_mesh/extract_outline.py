#!/usr/bin/env python3
"""Extract a silhouette-like outline from a photo and generate a 2D Gmsh mesh.

Goal: approximate the person as an obstacle for flow-past-body simulations (NektarF).

No OpenCV/skimage dependencies; uses PIL + numpy + scipy + matplotlib.

Pipeline (heuristic):
1) Load image, downsample for segmentation.
2) Create a "non-snow" mask via HSV/value threshold + saturation threshold.
3) Connected-components labeling; pick component whose centroid is closest to a target
   point in the image (defaults tuned for this photo: person on right).
4) Upsample mask to original size, smooth/close.
5) Extract polygon using matplotlib contour.
6) Simplify polygon (Ramer–Douglas–Peucker).
7) Write polygon points, diagnostic PNG, and a Gmsh .geo that creates a channel domain
   with the obstacle cut out.
8) Optionally run gmsh to generate .msh.

Usage:
  python extract_outline.py Jiachuan.jpg --outdir out

Key knobs:
  --target-x/--target-y: expected centroid (fraction of width/height)
  --H: obstacle height (simulation units)
  --domain-L/--domain-W: channel length/width in multiples of H
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def rgb_to_hsv(arr: np.ndarray) -> np.ndarray:
    """arr: float in [0,1], shape (H,W,3) -> hsv in [0,1]."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx = np.max(arr, axis=-1)
    mn = np.min(arr, axis=-1)
    diff = mx - mn

    h = np.zeros_like(mx)
    s = np.zeros_like(mx)
    v = mx

    # saturation
    s[mx > 0] = diff[mx > 0] / mx[mx > 0]

    # hue
    mask = diff > 1e-8
    idx = (mx == r) & mask
    h[idx] = ((g[idx] - b[idx]) / diff[idx]) % 6
    idx = (mx == g) & mask
    h[idx] = ((b[idx] - r[idx]) / diff[idx]) + 2
    idx = (mx == b) & mask
    h[idx] = ((r[idx] - g[idx]) / diff[idx]) + 4
    h = h / 6.0
    return np.stack([h, s, v], axis=-1)


def rdp(points: np.ndarray, eps: float) -> np.ndarray:
    """Ramer–Douglas–Peucker polyline simplification."""
    if len(points) < 3:
        return points

    # line from first to last
    a = points[0]
    b = points[-1]
    ab = b - a
    denom = np.linalg.norm(ab) + 1e-12

    # perpendicular distances
    ap = points - a
    # 2D cross product magnitude divided by |ab|
    d = np.abs(ab[0] * ap[:, 1] - ab[1] * ap[:, 0]) / denom
    i = int(np.argmax(d))
    dmax = float(d[i])

    if dmax > eps:
        left = rdp(points[: i + 1], eps)
        right = rdp(points[i:], eps)
        return np.vstack([left[:-1], right])
    else:
        return np.vstack([a, b])


def choose_component(mask: np.ndarray, target_xy: Tuple[float, float]) -> np.ndarray:
    lab, n = ndimage.label(mask)
    if n == 0:
        raise RuntimeError('No components found; adjust thresholds')

    # compute centroid for each component
    slices = ndimage.find_objects(lab)
    H, W = mask.shape
    tx, ty = target_xy
    best = None
    best_score = None
    for k, sl in enumerate(slices, start=1):
        comp = (lab[sl] == k)
        area = int(comp.sum())
        if area < 200:  # too small
            continue
        ys, xs = np.nonzero(comp)
        # coordinates in full image
        ys = ys + sl[0].start
        xs = xs + sl[1].start
        cx = xs.mean() / W
        cy = ys.mean() / H

        # score: distance to target + small penalty for huge blobs
        dist = (cx - tx) ** 2 + (cy - ty) ** 2
        score = dist + 1e-8 * area
        if best_score is None or score < best_score:
            best_score = score
            best = (lab == k)
    if best is None:
        raise RuntimeError('No suitable component found; adjust target/thresholds')
    return best


def extract_polygon_from_mask(mask: np.ndarray) -> np.ndarray:
    """Return Nx2 polygon (x,y) in pixel coordinates from binary mask."""
    # matplotlib contour expects (row,col). We'll contour at 0.5
    fig = plt.figure(figsize=(6, 6), dpi=150)
    ax = fig.add_subplot(111)
    cs = ax.contour(mask.astype(float), levels=[0.5])
    plt.close(fig)

    # pick longest path
    best = None
    best_len = 0
    for col in cs.collections:
        for p in col.get_paths():
            v = p.vertices
            if v.shape[0] > best_len:
                best_len = v.shape[0]
                best = v
    if best is None:
        raise RuntimeError('No contour path extracted')

    # vertices are (row, col) => (y,x)
    poly = np.stack([best[:, 1], best[:, 0]], axis=1)
    return poly


def write_geo(
    out_geo: Path,
    poly_xy: np.ndarray,
    H: float,
    domain_L: float,
    domain_W: float,
    upstream: float,
    downstream: float,
    lc_body: float,
    lc_far: float,
    center: Tuple[float, float],
):
    """Write a 2D gmsh .geo using a spline obstacle inside a rectangular channel."""
    # normalize polygon: shift to center, scale so height=H
    x = poly_xy[:, 0]
    y = poly_xy[:, 1]

    # image y grows downward; flip so y up
    y = -y

    # center to (0,0)
    cx, cy = center
    x = x - cx
    y = y - cy

    # scale so obstacle height = H
    height = y.max() - y.min()
    if height <= 0:
        raise RuntimeError('Bad polygon height')
    s = H / height
    x *= s
    y *= s

    # domain extents (relative to body height):
    # place body at x=0, y=0; channel is [-upstream, downstream] x [-W/2, W/2]
    Lx0 = -upstream * H
    Lx1 = downstream * H
    Wy0 = -0.5 * domain_W * H
    Wy1 = 0.5 * domain_W * H

    # pick a manageable number of points for spline
    # ensure closed loop
    if np.linalg.norm([x[0] - x[-1], y[0] - y[-1]]) > 1e-6:
        x = np.r_[x, x[0]]
        y = np.r_[y, y[0]]

    with out_geo.open('w') as f:
        f.write('// Auto-generated from photo silhouette\n')
        # Use the built-in GEO kernel (more tolerant for long splines).
        f.write('\n')
        f.write(f'H = {H};\n')
        f.write(f'lc_body = {lc_body};\n')
        f.write(f'lc_far  = {lc_far};\n\n')

        # outer rectangle
        f.write(f'Point(1) = {{{Lx0}, {Wy0}, 0, lc_far}};\n')
        f.write(f'Point(2) = {{{Lx1}, {Wy0}, 0, lc_far}};\n')
        f.write(f'Point(3) = {{{Lx1}, {Wy1}, 0, lc_far}};\n')
        f.write(f'Point(4) = {{{Lx0}, {Wy1}, 0, lc_far}};\n')
        f.write('Line(1) = {1,2};\n')
        f.write('Line(2) = {2,3};\n')
        f.write('Line(3) = {3,4};\n')
        f.write('Line(4) = {4,1};\n')
        f.write('Curve Loop(10) = {1,2,3,4};\n')

        # obstacle points
        base_id = 100
        for i, (xi, yi) in enumerate(zip(x, y)):
            pid = base_id + i
            f.write(f'Point({pid}) = {{{xi}, {yi}, 0, lc_body}};\n')
        f.write('\n')

        # spline loop: split into multiple splines to guarantee a closed loop
        ids = [base_id + i for i in range(len(x))]
        # drop repeated last point if present
        if ids[0] == ids[-1]:
            ids = ids[:-1]

        n = len(ids)
        ns = max(4, min(12, n // 20))  # 4..12 splines
        cuts = [int(round(k * n / ns)) for k in range(ns + 1)]
        spline_ids = []
        sid0 = 20
        for si in range(ns):
            a = cuts[si]
            b = cuts[si + 1]
            chunk = ids[a:b]
            if si > 0:
                # include previous endpoint to ensure continuity
                chunk = [ids[a - 1]] + chunk
            if si == ns - 1:
                # close to first point
                chunk = chunk + [ids[0]]
            if len(chunk) < 2:
                continue
            sid = sid0 + si
            spline_ids.append(sid)
            f.write(f'Spline({sid}) = {{{", ".join(map(str, chunk))}}};\n')

        f.write(f'Curve Loop(21) = {{{", ".join(map(str, spline_ids))}}};\n')

        f.write('Plane Surface(30) = {10, 21};\n')
        f.write('\n// Physical groups\n')
        f.write('Physical Surface("fluid") = {30};\n')
        f.write('Physical Curve("inlet")  = {4};\n')
        f.write('Physical Curve("outlet") = {2};\n')
        f.write('Physical Curve("wall")   = {1,3};\n')
        f.write(f'Physical Curve("body")   = {{{", ".join(map(str, spline_ids))}}};\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image', type=Path)
    ap.add_argument('--outdir', type=Path, default=Path('out_person'))

    ap.add_argument('--downsample', type=int, default=4, help='Downsample factor for segmentation')
    ap.add_argument('--vmax-snow', type=float, default=0.82, help='Value threshold to reject snow (HSV V)')
    ap.add_argument('--smin-color', type=float, default=0.12, help='Saturation threshold to catch jacket etc')
    ap.add_argument('--target-x', type=float, default=0.72, help='Expected centroid x (fraction of width)')
    ap.add_argument('--target-y', type=float, default=0.33, help='Expected centroid y (fraction of height)')

    ap.add_argument('--H', type=float, default=1.0, help='Obstacle height in simulation units')
    ap.add_argument('--domain-L', type=float, default=20.0, help='Domain length in multiples of H')
    ap.add_argument('--domain-W', type=float, default=10.0, help='Domain width in multiples of H')
    ap.add_argument('--upstream', type=float, default=5.0, help='Upstream length in H')
    ap.add_argument('--downstream', type=float, default=15.0, help='Downstream length in H')
    ap.add_argument('--lc-body', type=float, default=0.03, help='Mesh size near body (in units)')
    ap.add_argument('--lc-far', type=float, default=0.3, help='Mesh size far-field (in units)')

    ap.add_argument('--simplify', type=float, default=2.0, help='RDP epsilon in pixels (after upsample)')
    ap.add_argument('--no-gmsh', action='store_true', help='Do not run gmsh')

    args = ap.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    im = Image.open(args.image).convert('RGB')
    arr0 = np.asarray(im).astype(np.float32) / 255.0
    H0, W0, _ = arr0.shape

    # downsample
    ds = max(1, args.downsample)
    arr = arr0[::ds, ::ds, :]
    hsv = rgb_to_hsv(arr)

    V = hsv[..., 2]
    S = hsv[..., 1]

    # non-snow heuristic: not too bright OR fairly saturated
    non_snow = (V < args.vmax_snow) | (S > args.smin_color)

    # remove tiny speckles
    non_snow = ndimage.binary_opening(non_snow, iterations=1)

    # Focus on a region-of-interest around the person to avoid selecting the whole scene.
    h, w = non_snow.shape
    x0 = int(0.52 * w)
    x1 = int(0.92 * w)
    y0 = int(0.12 * h)
    y1 = int(0.62 * h)
    roi = np.zeros_like(non_snow, dtype=bool)
    roi[y0:y1, x0:x1] = True

    comp = choose_component(non_snow & roi, (args.target_x, args.target_y))

    # grow/close a bit
    comp = ndimage.binary_closing(comp, iterations=2)
    comp = ndimage.binary_fill_holes(comp)

    # upsample mask back
    mask = np.kron(comp.astype(np.uint8), np.ones((ds, ds), dtype=np.uint8))
    mask = mask[:H0, :W0].astype(bool)

    # smooth mask edges
    mask = ndimage.binary_closing(mask, iterations=2)
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_fill_holes(mask)

    poly = extract_polygon_from_mask(mask)

    # simplify (treat contour as open polyline; avoid duplicate first/last degeneracy)
    if len(poly) >= 3 and np.linalg.norm(poly[0] - poly[-1]) < 1e-6:
        poly_open = poly[:-1]
    else:
        poly_open = poly
    poly_s = rdp(poly_open, eps=float(args.simplify))
    # close
    if np.linalg.norm(poly_s[0] - poly_s[-1]) > 1e-6:
        poly_s = np.vstack([poly_s, poly_s[0]])

    # compute center (use mask centroid)
    ys, xs = np.nonzero(mask)
    cx = xs.mean() if len(xs) else W0 / 2
    cy = ys.mean() if len(ys) else H0 / 2

    # write diagnostics
    # overlay
    fig = plt.figure(figsize=(6, 8), dpi=150)
    ax = fig.add_subplot(111)
    ax.imshow(arr0)
    ax.contour(mask.astype(float), levels=[0.5], colors='y', linewidths=1)
    ax.plot(poly_s[:, 0], poly_s[:, 1], 'r-', linewidth=1)
    ax.set_axis_off()
    fig.tight_layout(pad=0)
    fig.savefig(outdir / 'outline_overlay.png')
    plt.close(fig)

    np.savetxt(outdir / 'outline_pixels.csv', poly_s, delimiter=',', header='x_px,y_px', comments='')

    # write geo
    out_geo = outdir / 'person_channel.geo'
    write_geo(
        out_geo,
        poly_s,
        H=float(args.H),
        domain_L=float(args.domain_L),
        domain_W=float(args.domain_W),
        upstream=float(args.upstream),
        downstream=float(args.downstream),
        lc_body=float(args.lc_body),
        lc_far=float(args.lc_far),
        center=(float(cx), float(cy)),
    )

    print(f'WROTE {outdir / "outline_overlay.png"}')
    print(f'WROTE {outdir / "outline_pixels.csv"}')
    print(f'WROTE {out_geo}')

    if not args.no_gmsh:
        import subprocess
        msh2 = outdir / 'person_channel.msh'
        cmd = ['gmsh', '-2', str(out_geo), '-format', 'msh2', '-o', str(msh2)]
        print('RUN:', ' '.join(cmd))
        subprocess.check_call(cmd)
        print(f'WROTE {msh2}')


if __name__ == '__main__':
    main()
