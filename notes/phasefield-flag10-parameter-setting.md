# PhaseField parameter setting (Flag 10) — reference note

Date: 2026-03-24

## Source of dimensional inputs
- Script: `/users/zwang197/PhaseField/Dimen_Chan3D.py`
- Dataset: `../Purdue_Data/new_data/METHODS_MURI_AllTestCases_Updated_2-19-2026.xlsx`
- Flag 10 row used in script:
  - `avg_mass_flux = 161.484372323411`
  - `avg_heat_flux_w_cm2 = 4.5206123131806004`
  - `Tin_C = 72.299979219331107`
  - `subcool_C = 3.7000207805150498`

## Characteristic scales used
- `L_infty = 2.0e-3` m (2 mm)
- `U_infty = G / rho_2`
- `T_infty = T_sat`

## Important nondimensional outputs used for .rea
- `rho_2/rho_1 = 1596.6666666666667`
- `mu_1_d = 0.06080774169486883`
- `mu_2/mu_1 = 22.926829268292686`
- `k_1_d = 0.05885379567834768`
- `k_2/k_1 = 27.32`
- `cp_2/cp_1 = 2.0`
- `sigma_d = 1730.377200489894`
- `hlv_d = 3.078223986144575`
- `g_d = 0.6905084882768486`
- `T_init = Tin/Tsat = 0.9894027759400926`
- `DeltaT_d = 0.014320492624952608`
- `qh1_d = 0.01828109110190613`

## Mapping used in `muri_all.rea`
- `DENSITY_RATIO` <- `rho_2/rho_1`
- `VISCOSITY_1` <- `mu_1_d`
- `VISCOSITY_RATIO` <- `mu_2/mu_1`
- `THERMAL_CONDUCTIVITY_1` <- `k_1_d`
- `THERMAL_CONDUCTIVITY_RATIO` <- `k_2/k_1`
- `SPECIFIC_HEAT_RATIO` <- `cp_2/cp_1`
- `SURFACE_TENSION`, `TENSION` <- `sigma_d` (dimensionless)
- `DLATENT_HEAT` <- `hlv_d`
- `G0` <- `g_d`
- `DFLUX_WALL`, `DHEATER_SOURCE` <- `qh1_d` (with sign convention in case file)
- `DLIQUID_SAT_TEMP` <- `T_sat` (as currently used by this case setup)
- `DBOILING_TEMP_DELTA` <- `DeltaT_d`

## Caution
- In this setup, `SURFACE_TENSION/TENSION` are treated as **dimensionless** and populated with `sigma_d`.
- If a future solver branch expects dimensional sigma, this must be changed to SI value (`0.059`) consistently with the rest of normalization.
