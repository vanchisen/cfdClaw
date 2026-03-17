# Zhaojie duct_h1 periodic BC setup for `gmsh2rea.py`

## Target files
- GEO: `/users/zwang197/Works/Zhaojie/domain_extract/Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.geo`
- MSH: same basename with `.msh`
- REA: same basename with `.rea`

## Required periodic rule (strict)
`gmsh2rea.py` periodic matching (y-group) expects paired boundary face centers to satisfy:
- `x_left + x_right = 0`
- `y_left = y_right`

In practice:
1. Put paired periodic curves into physical groups 5 and 6.
2. Make left/right periodic sides mirror each other in `x` about 0.
3. Ensure both sides have identical y-span and point ordering consistency.

## Current duct_h1 normalization convention
- Inlet/outlet periodic edge height is scaled to `1.0`.
- Geometry was shifted/scaled so periodic side x-locations are symmetric (`-x0`, `+x0`).

## Regeneration commands
```bash
gmsh /users/zwang197/Works/Zhaojie/domain_extract/Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.geo \
  -2 -format msh2 \
  -o /users/zwang197/Works/Zhaojie/domain_extract/Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.msh

python3 /users/zwang197/.openclaw/workspace/picture9_mesh/gmsh2rea.py \
  --msh /users/zwang197/Works/Zhaojie/domain_extract/Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.msh \
  --rea /users/zwang197/Works/Zhaojie/domain_extract/Picture10_Ver2_domain_straightSegments_fullquad_lt6k_f1p15_periodic_leftW1.rea
```

## Quick validation
- Confirm periodic edge heights are equal (normalized case: both `1.0`).
- Confirm periodic x midpoints are opposite (`xL + xR = 0`).
- Run `gmsh2rea.py`; conversion must complete without periodic pairing errors.
