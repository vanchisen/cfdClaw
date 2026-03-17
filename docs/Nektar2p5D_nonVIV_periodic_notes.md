# Nektar2.5D (non-VIV) simulation notes

## 1) Compile for simulation (without VIV coupling workflow)

Use the project `ReadMe.txt` order exactly:

1. `cd Nektar2.5D/GS && source compile`
2. `cd Nektar2.5D/rfftw && source compile`
3. `cd Nektar2.5D/Veclib && source compile`
4. `cd Nektar2.5D/Hlib/Linux && source compile`
5. `cd Nektar2.5D/SPM_Thermo/Linux && source compile`
6. `cd Nektar2.5D/Utilities/Linux && source compile`

For non-VIV simulation runs, use **`nektarF`** (not `flexF`).

---

## 2) Mesh preparation workflow

1. Build geometry/mesh in Gmsh (`.geo` -> `.msh`, MSH2 format).
2. Keep boundary physical groups explicit:
   - periodic side A: `Physical Curve(3)`
   - periodic side B: `Physical Curve(4)`
   - walls: `Physical Curve(7)`
   - obstacle wall: `Physical Curve(8)`
   - fluid surface: `Physical Surface(10)`
3. Convert mesh to Nektar `.rea`:

```bash
python3 /users/zwang197/.openclaw/workspace/picture9_mesh_scaled/gmsh2rea_picture9.py --msh <mesh.msh> --rea <case.rea>
```

---

## 3) Parameter changes in `.rea`

Typical edits used for this case:

- `KINVIS = 10.0` (for `Re = 0.1` with unit-scale reference)
- `MODES = 3`
- `LQUAD = 5`
- `MQUAD = 5`

---

## 4) Periodic flow-direction setup + driving force

If flow direction is periodic (inlet/outlet periodic), use pressure-gradient driving in **DRIVE FORCE** section:

- `FFX = <value>` (streamwise forcing, e.g. `1.0`)
- `FFY = 0.0`
- `FFZ = 0.0`

Important for non-VIV usage in this workflow:

- keep `FORCX` / `FORCY` as VIV-control fields (do not use them as flow driver)
- use `FFX` as the primary streamwise driver for periodic flow

---

## 5) 2D run command

```bash
mpirun -np 1 /users/zwang197/Works/NeuroSEM/OpenClaw/Nektar2.5D/SPM_Thermo/Linux/nektarF -chk -z2 -S cyl.rea > out 2>&1
```

Notes:
- this branch warns that dealiasing prefers `z` multiple of 4; for 2D workflow we still use `-z2` as requested.
- run from a dedicated case folder (with `cyl.rea`).

---

## 6) Detailed note: how periodic BC was handled for Nektar2.5D in this project

### Scope
This documents the **exact approach used here** for `Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic.geo` and derived cases.

### A. Periodic handling method used
I used a **BC-tag pairing method** (solver-side periodic interpretation), not geometric tie constraints in Gmsh.

Concretely:
- left boundary group: `Physical Curve(3)`
- right boundary group: `Physical Curve(4)`
- walls: `Physical Curve(7)`
- obstacle wall: `Physical Curve(8)`

The left/right periodic pair is therefore represented by boundary IDs `(3,4)` in the converted `.rea` workflow.

### B. What I did **not** do
I did **not** add Gmsh native periodic constraints such as:

```geo
Periodic Curve{right_ids...} = {left_ids...} Translate{Lx,0,0};
```

So the mesh is not node-tied by Gmsh periodic mapping; periodicity is imposed by boundary-condition pairing convention after conversion.

### C. How left/right sets were identified
For the straight-segment geometry build, outer boundary lines were split by x-location:
- curves near `xmin` -> left set (`Physical Curve(3)`)
- curves near `xmax` -> right set (`Physical Curve(4)`)
- remaining outer curves -> wall set (`Physical Curve(7)`)
- obstacle loop kept as `Physical Curve(8)`

### D. Scaling and periodic tags
When geometry was scaled to make left-boundary width = 1:
- only `Point(...)` coordinates (and point `lc`) were scaled isotropically
- line IDs and physical groups were preserved
- therefore periodic pair tags `(3,4)` remained unchanged and valid

### E. Conversion implication (`.msh` -> `.rea`)
The converter (`gmsh2rea_picture9.py`) preserves physical-group IDs into boundary group IDs used by the `.rea`.

Therefore periodic interpretation depends on using matching periodic pair IDs consistently in the solver setup, not on Gmsh periodic-node linking.

### F. Practical checks before run
1. In `.geo`, verify both groups exist and are non-empty:
   - `Physical Curve(3)` and `Physical Curve(4)`
2. Confirm they correspond to opposite streamwise boundaries (left/right).
3. Ensure wall groups (`7`, `8`) are not mixed into periodic groups.
4. After conversion, verify the `.rea` boundary sections carry these groups correctly.
5. Use x-driving force (`FFX`) for periodic streamwise flow; keep VIV flags (`FORCX/FORCY`) as VIV-only controls.

### G. Known limitation of this method
Because Gmsh periodic tie was not enforced, if left/right discretizations become inconsistent in future geometry edits, periodic BC quality can degrade.

If strict node-to-node periodicity is needed, add explicit Gmsh `Periodic Curve` constraints and regenerate mesh.

### H. Recommendation for future maintenance
- Keep the periodic pair IDs fixed as `(3,4)` across all variants.
- Any geometry refactor should re-check left/right curve membership.
- If solution sensitivity appears at periodic interface, upgrade to explicit Gmsh periodic mapping.
