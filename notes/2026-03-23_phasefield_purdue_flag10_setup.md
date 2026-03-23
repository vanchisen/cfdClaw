# Phase-field validation setup note (Purdue dataset)

Date: 2026-03-23

## Validation case selected

- Dataset: `11_14_2025`
- Case: `Flag 10`
- Type: `Experiment`

Raw files:
- Phase: `11_14_BinaryPhase/CompressedBinaryPhase__11_14_25_Flag10_0_12006.h5`
- Temperature: `11_14_Temperature/TempProcessed_11_14_25_Flag10_0_2000.mat`

Sync relation used:
- `phase_index = 6*(temperature_index - 1)`

Generated visualization:
- `new_data/Flag10_temp_phase_synced_plot.png`

## Key experimental conditions (Flag 10)

From `METHODS_MURI_AllTestCases_Updated_2-19-2026.xlsx`:

- `avg_mass_flux = 161.48437232341101`
- `avg_heat_flux = 4.5206123131806004` (W/cm², converted as needed in scripts)
- `avg_inlet_subcool = 3.7000207805150498`
- `avg_inlet_temperature = 72.299979219331107 °C`
- `avg_outlet_temperature = 73.304246730066893 °C`
- `avg_heater_power = 4.9726735285919696`
- `avg_differential_pressure = 27.697730766468201`
- `avg_inlet_pressure = 96.885174134883002`
- `avg_outlet_pressure = 96.888746404013403`

Inferred saturation temperature for this case:
- `Tsat ≈ Tin + subcooling ≈ 76.00 °C = 349.15 K`

Background pressure for nucleation model input:
- use ~`0.10 MPa` (from ~96.9 kPa inlet/outlet pressure, clipped to Chen correlation lower bound)

## Nucleation model alignment (without changing phase-change closure)

Code path:
- `~/Codes/PhaseFieldCode/P_Nektar3d/src/boiling_model.C`
- legacy consistency block: `~/Codes/PhaseFieldCode/P_Nektar3d/src/phase_coupled.C`

Applied updates:

1. Fixed active nucleation density coefficient sign:
   - from `B = -0.122*P + 1.988`
   - to   `B = 0.122*P + 1.988`

2. Pressure handling parameterized:
   - preferred: `DBACKGROUND_PRESSURE_MPA`
   - fallback: `DBACKGROUND_PRESSURE_PA` (auto-converted to MPa)
   - fallback default if unset
   - clamped to Chen validity window `[0.10, 19.8] MPa`

3. Activation logic changed:
   - no longer blindly activates sequential sites
   - activates based on local threshold
   - new threshold parameter: `DACTIVATION_SUPERHEAT`

4. Activation threshold unit consistency:
   - local delta now uses Kelvin-scale conversion:
   - `local_dT = (active_bubble_temperature - T_sat) * T_infty`
   - so `DACTIVATION_SUPERHEAT` is interpreted in K

## Nondimensionalization consistency notes

Reference script:
- `/users/zwang197/PhaseField/Dimen_Chan3D.py`

Current convention used:
- Temperature is nondimensionalized by `T_infty`, with `T_infty = T_sat`
- This supports conversion from solver temperature delta to physical K via
  `ΔT_phys = (T* - Tsat*) * T_infty`

## Geometry notes

From Y.J. Chen paper:
- solid plate thickness at channel base: `0.6 mm`

From Purdue metadata for this dataset:
- channel height: `5.25 mm`
- channel width: `2.2 mm`

## Next setup item

- Add unheated inlet and unheated outlet channel sections around heated test section
  (piecewise wall heat flux + matching nucleation window to heated region).
