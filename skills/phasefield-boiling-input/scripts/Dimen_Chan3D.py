import math

# ================================================================
# Dimensional -> Dimensionless parameters for PhaseField Channel 3D
# Updated using Purdue experimental case: 11_14_2025, Flag 10
# ================================================================

# ---------------------------
# Experimental case inputs
# ---------------------------
avg_mass_flux = 161.48437232341101   # kg/(m^2 s)
avg_heat_flux_w_cm2 = 4.5206123131806004  # W/cm^2 (dataset convention)

Tin_C = 72.299979219331107           # degC (Flag 10 selected row in METHODS sheet)
subcool_C = 3.7000207805150498       # K (same row; same magnitude in C)

# Derived saturation from experiment
Tsat_C = Tin_C + subcool_C            # ~76.00 C

# Convert to SI
qh = avg_heat_flux_w_cm2 * 1.0e4      # W/m^2
Tin = Tin_C + 273.15                  # K
T_sat = Tsat_C + 273.15               # K

# ---------------------------
# Model / fluid properties (working fluid: 3M Novec HFE-7200)
# values aligned with local reference: Dimen_NucleationTest_HFE7200.m
# ---------------------------
lz = 5e-7
qs = qh / lz

rho_1 = 10.13      # vapor density  (kg/m^3)
rho_2 = 1325.0     # liquid density (kg/m^3)

mu_1 = 1.035e-5
mu_2 = 3.79e-4

cp_1 = 972.2
cp_2 = 1333.0

k_1 = 0.01436
k_2 = 0.07966

# solid layers
rho_3 = 3980
cp_3 = 929
k_3 = 25.1

rho_4 = 4510
cp_4 = 544
k_4 = 17

sigma = 0.01299
hlv = 108.8e3
R_g = 8.314
g = 9.81

# Reference length scale
R0 = 200e-6
R1 = R0
channel_width = 2.0e-3  # characteristic length set to 2.0 mm
L_infty = channel_width

exp_chan_width = 2.2e-3 
exp_chan_height = 5.25e-3 


# Velocity scale from experimental mass flux
U_infty = avg_mass_flux / rho_2

# temperature scale choice (same convention as previous script)
T_infty = T_sat

# Optional imposed wall overheating used in setup
Delta_T = 5.0
T_a = T_sat + Delta_T
T_inlet = Tin

# ---------------------------
# Auxiliary constants
# ---------------------------
Ca = 0.5 * (cp_1 - cp_2)
Cb = 0.5 * (cp_1 + cp_2)
Ra = 0.5 * (rho_1 - rho_2)
Rb = 0.5 * (rho_1 + rho_2)
Ka = 0.5 * (k_1 - k_2)
Kb = 0.5 * (k_1 + k_2)

Cr = Cb / Ca
Kr = Kb / Ka
Rr = Rb / Ra

disc = (Kr - Rr) / (Kr - Cr)
phi_m = -0.5 * (Rb / Ra + Cb / Ca)

eta = 1.0 / 32.0
Delta_T_d = Delta_T / T_sat

dT_dn = (qh / k_2) / T_sat * L_infty

# ---------------------------
# Nondimensionalization
# ---------------------------
cp_infty = cp_1
rho_infty = rho_1

t_scale = L_infty / U_infty
X = cp_infty * T_infty / (U_infty * U_infty)

rho_r = rho_2 / rho_infty
mu_r = mu_2 / mu_1
cp_r = cp_2 / cp_1
k_r = k_2 / k_1

qh_d = qh / (T_sat * rho_infty * cp_infty * U_infty)
qs_d = qs / (T_sat * rho_infty * cp_infty * U_infty / L_infty)

rho_1_d = rho_1 / rho_infty
cp_1_d = cp_1 / cp_infty

T_d = T_a / T_sat
T_dI = T_inlet / T_sat
sigma_d = sigma / (rho_infty * U_infty * U_infty * L_infty)
mu_1_d = mu_1 / (rho_infty * U_infty * L_infty)
k_1_d = k_1 / (rho_infty * cp_infty * U_infty * L_infty)
hlv_d = hlv / (cp_infty * T_infty)
g_d = g * L_infty / (U_infty * U_infty)

R_g_d = R_g / (U_infty * U_infty / T_infty)

Re_1 = U_infty * rho_1 * R0 / mu_1
Re_2 = U_infty * rho_2 * R0 / mu_2
We_1 = rho_1 * U_infty * U_infty * R0 / sigma
We_2 = rho_2 * U_infty * U_infty * R0 / sigma
Pr_1 = mu_1 * cp_1 / k_1
Ja_1 = rho_2 * cp_2 * Delta_T / rho_1 / hlv

r_bubble = L_infty
Bo_1 = g * r_bubble * r_bubble * rho_2 / sigma

mu_2_d = mu_1_d * mu_r
rho_2_d = rho_2 / rho_infty
cp_2_d = cp_2 / cp_infty
k_2_d = k_1_d * k_r

Pr = cp_2_d * mu_2_d / k_2_d
tB = 5.0 * math.sqrt(mu_2_d / rho_2_d) * math.pow(Pr, -1.0 / 3.0)
alpha_2 = k_2 / (rho_2 * cp_2)
alpha_2_d = k_2_d / (rho_2_d * cp_2_d)

rho_3_d = rho_3 / rho_infty
cp_3_d = cp_3 / cp_infty
k_3_d = k_1_d * k_3 / k_1

rho_4_d = rho_4 / rho_infty
cp_4_d = cp_4 / cp_infty
k_4_d = k_1_d * k_4 / k_1

alpha_fluid = 0.5 * max(k_1_d, k_2_d) / min(rho_1_d * cp_1_d, rho_2_d * cp_2_d)
alpha_solid_couple = max(k_2_d, k_3_d, k_4_d) / min(rho_2_d, rho_3_d, rho_4_d) / min(cp_2_d, cp_3_d, cp_4_d)

# geometric/thermal-resistance settings (kept from previous script)
L1_d = 1.3e-3 / L_infty
L2_d = 5e-7 / L_infty
L3_d = 1e-3 / L_infty

R1 = L1_d / k_2_d
R2 = L2_d / k_3_d + L3_d / k_4_d

qh1_d = R2 / (R1 + R2) * qh_d

# mesh / timestep estimation helpers
zMin = 0.01 / 4.0
uMax = 3.5
cAdv = 1.0
cSigma = 1.0

# ---------------------------
# Print summary
# ---------------------------
print('=== Experimental inputs (Flag 10) ===')
print('Tin [K]: ', Tin)
print('Tsat [K]: ', T_sat)
print('Mass flux G [kg/m^2/s]: ', avg_mass_flux)
print('Heat flux qh [W/m^2]: ', qh)
print('U_infty [m/s]: ', U_infty)

print('\n=== Reference scales ===')
print('L_infty: ', L_infty)
print('U_infty: ', U_infty)
print('T_infty: ', T_infty)
print('t_scale: ', t_scale)

print('\n=== Dimensionless property groups ===')
print('channel width: ', exp_chan_width/L_infty)
print('channel height: ', exp_chan_height/L_infty)
print('rho_1_d: ', rho_1_d)
print('rho_2_d: ', rho_2_d)
print('mu_1_d: ', mu_1_d)
print('mu_2_d: ', mu_2_d)
print('k_1_d: ', k_1_d)
print('k_2_d: ', k_2_d)
print('cp_1_d: ', cp_1_d)
print('cp_2_d: ', cp_2_d)
print('sigma_d: ', sigma_d)
print('hlv_d: ', hlv_d)
print('g_d: ', g_d)
print('R_g_d: ', R_g_d)

print('\n=== Thermal / flow parameters ===')
print('T_init (Tin/Tsat): ', T_dI)
print('T_wall ((Tsat+Delta_T)/Tsat): ', T_d)
print('Delta_T_d: ', Delta_T_d)
print('qh_d: ', qh_d)
print('qh1_d: ', qh1_d)
print('qs_d: ', qs_d)
print('alpha_fluid: ', alpha_fluid)
print('alpha_solid_couple: ', alpha_solid_couple)

print('\n=== Dimensionless groups ===')
print('Re_1: ', Re_1)
print('Re_2: ', Re_2)
print('We_1: ', We_1)
print('We_2: ', We_2)
print('Pr_1: ', Pr_1)
print('Ja_1: ', Ja_1)
print('Bo_1: ', Bo_1)
print('Pr (liq, nondim form): ', Pr)
print('tB: ', tB)

print('\n=== Geometry / numerics ===')
print('heater thickness (nondim): ', 0.5e-6 / L_infty)
print('solid thickness (nondim): ', 1e-3 / L_infty)
print('bubble init radius (nondim): ', (30 / 2) / 2000)
print('Time step Adv: ', cAdv * zMin / uMax)
print('Time step Sigma: ', cSigma * math.sqrt((rho_1_d + rho_2_d) * zMin * zMin * zMin / sigma_d))
print('Max boiling rate on Nektar: ', 1.0 / math.sqrt(2) / eta * Delta_T_d / math.sqrt(2) / eta / hlv_d)
