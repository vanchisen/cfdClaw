# Re30K_Ma2.0 restart stabilization playbook (mesh-interpolated restart)

Date: 2026-03-24

## Problem
Direct restart from interpolated state (`restart.h5`) on `Cylinder_Re30K_mesh.h5` was unstable and blew up within ~10–20 steps (NaN velocity / huge timestep).

## Root symptom
- Early-time high-frequency noise from restart interpolation.
- `aFV` dropped to near 0 and solution switched effectively to DG too early.
- Then NaNs appeared quickly.

## Working recovery chain
1. Keep original restart untouched.
2. Create smoothed restart (`restart_smoothed_a015.h5`) by damping subcell oscillations in `DG_Solution`:
   - Dataset shape: `(137088, 9, 9, 9, 5)`
   - Per-element smoothing:
     - `U_new = (1-alpha)*U + alpha*mean(U_elem)` with `alpha = 0.15`
   - Positivity guard:
     - `rho` (`var0`) and `E` (`var4`) clipped to `>= 1e-8`
3. Launch **stage0 forced-FV** startup from smoothed restart:
   - `parameter_flexi_stage0_forcedFV.ini`
   - Key settings:
     - `FV_alpha_min = 1.0`
     - `FV_alpha_max = 1.0`
     - `CFLscale = 0.03`, `DFLscale = 0.03`, `dt = 1e-6`
     - short horizon: `tend = 560.0005`
     - stronger dissipation: `EVM_alpha = 30.0`, `EVM_beta = 1.2`
     - `RP_inUse = F`, time-avg off
4. Launch **stage2 ramp** from latest stage0 state:
   - `parameter_flexi_stage2_ramp.ini`
   - restart source example:
     - `Cylinder_Re30K_stage0_forcedFV_State_0000560.000500000.h5`

## Files created in `/users/zwang197/Works/Compressible/Re30K_Ma2.0`
- `restart_smoothed_a015.h5`
- `parameter_flexi_stage0_forcedFV.ini`
- `parameter_flexi_stage1_settle.ini`
- `parameter_flexi_stage1b_settle_strong.ini`
- `parameter_flexi_stage2_ramp.ini`
- logs:
  - `out_stage0_forcedFV_smooth`
  - `out_stage2_ramp`

## Practical guidance
- For mesh-interpolated restarts, prefer **smooth + forced-FV startup** before normal ramp/production.
- Keep recordpoints/time-averaging off during stabilization.
- After stage2 is stable, handoff to production ini (or optional stage3 transition).
