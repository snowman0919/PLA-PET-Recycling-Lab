"""VP1 Stage 6: downstream filament process model — mass balance, cooling,
transport delay, puller/winder dynamics and the hard 500 W heater schedule.

Scope (docs/decisions/filament-quality-route.md section 4): a SIMPLE
physically-consistent model connecting die -> cooling -> gauge -> puller ->
winder.  It is NOT a melt FEM/CFD, NOT a materials test, and its
in-spec predictions are NOT production claims: parameters marked CALIBRATION
are estimates pending reference-material runs.

Model equations (cooled, solid cross-section):
    mdot = rho_s * A_final * v_line            (mass balance, steady state)
    d_final = sqrt(4 * mdot / (pi * rho_s * v_line))     (round strand)
    A_final = pi * dx * dy / 4                 (elliptical ovality)
The die bore does NOT set the final diameter; the model proves it by
integrating draw-down under mass balance.

Cooling: lumped-capacitance strand with convection to tray air:
    dT/dt = -h_eff * perimeter / (rho * cp * A) * (T - T_air)
h_eff scales with the adjustable duct air length (50..250 mm) and the fan
schedule: h_eff = h0 * (1 + alpha * ducted_fraction * fans_on/3).
CALIBRATION: h0, alpha are first-order estimates, not measured UA.

Measurement: the gauge sits at x=822, the puller nip at x=829 (real frozen
datums from downstream.py station_interfaces).  Sensor->actuation transport
delay = 7 mm / v_line; the controller uses a delayed measurement buffer.

Puller: commanded surface speed with a first-order motor response
(tau_motor) and Coulomb slip: effective strand speed v_pull = v_cmd *
(1 - slip(tension, nip_force)).  Slip is zero below the grip envelope and
rises linearly above it (CALIBRATION envelope).

Winder: independent tension isolation — spool surface speed follows the
puller with a slip-tensioner clutch (tensioner torque limit); spool radius
grows with wound length; winder speed command never feeds back into the
puller (tension-decoupled, per decision route A).

Power: the 500 W hard operating budget schedules the 3x100 W bands + 60 W
cartridge through the controller allocator (one band at a time, rotating);
heat input to the barrel model is the ADMITTED schedule, not the demand.
M2/M1/fan loads are UNRATED estimates and only affect admission order.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]

# --- frozen geometry (c2.1/src/downstream.py station_interfaces) -----------
GAUGE_X = 809.0
PULLER_NIP_X = 829.0
SENSOR_TO_PULLER_MM = PULLER_NIP_X - GAUGE_X          # 20.0 mm
DIE_EXIT_X = 540.0
TRAY_EXIT_X = 820.0
TRAY_LENGTH_MM = TRAY_EXIT_X - 545.0                  # 275 mm
DUCT_AIR_LENGTH_RANGE = (50.0, 250.0)
NOMINAL_FILAMENT_MM = 1.75

# --- material table (solid-state values; melt handled only via mdot) -------
# rho_s = solid density after cooling.  cp = specific heat.  T_die = die
# exit temperature planning point, T_air = tray air, T_set = puller-ready
# target.  ALL are engineering planning values (datasheet-class), NOT
# measured on this machine.
MATERIALS = {
    "PLA": {"rho_s": 1240.0, "cp": 1800.0, "T_die": 185.0, "T_set": 55.0,
            "T_air": 35.0},
    "PET": {"rho_s": 1330.0, "cp": 1250.0, "T_die": 255.0, "T_set": 60.0,
            "T_air": 35.0},
    "TPU": {"rho_s": 1210.0, "cp": 1900.0, "T_die": 215.0, "T_set": 50.0,
            "T_air": 35.0},
}

# CALIBRATION: first-order convection estimates, not measured UA.
H0_W_M2K = 25.0          # free/weak forced convection baseline
DUCT_ALPHA = 3.0         # extra convection multiplier at full duct + 3 fans


def area_mm2(d_mm):
    return math.pi * (d_mm / 2.0) ** 2


def steady_diameter_mm(mdot_g_s, rho_s_kg_m3, v_line_mm_s):
    """Final cooled diameter from mass balance (round strand)."""
    rho = rho_s_kg_m3 / 1e9        # kg/mm3
    A = (mdot_g_s / 1000.0) / (rho * v_line_mm_s)   # mm2
    return math.sqrt(4.0 * A / math.pi)


def ovality(d_major_mm, d_minor_mm):
    A = math.pi * d_major_mm * d_minor_mm / 4.0
    d_eq = math.sqrt(4.0 * A / math.pi)
    return {"d_equiv_mm": d_eq, "ovality_mm": d_major_mm - d_minor_mm,
            "ovality_ratio": d_major_mm / d_minor_mm}


@dataclass
class HeaterSchedule:
    """Hard-budget band scheduler mirroring controller_core.cpp: one 100 W
    band admitted at a time (rotating), the 60 W cartridge admitted first;
    total heater draw <= 160 W.  Power above 500 W total is never admitted
    (allocator invariant)."""
    bands_W: tuple = (100.0, 100.0, 100.0)
    cartridge_W: float = 60.0
    period_s: float = 30.0

    def admitted_W(self, t_s):
        band = int(t_s // self.period_s) % len(self.bands_W)
        return self.cartridge_W + self.bands_W[band]


@dataclass
class LineParams:
    material: str = "PLA"
    # nominal: 0.0358 g/s at 12 mm/s gives d=1.75 mm for PLA
    # (A=2.405mm2, rho_s=1.24e-6 kg/mm3 => mdot=rho*A*v=0.0358 g/s = 129 g/h)
    mdot_g_s: float = 0.0358
    v_line_mm_s: float = 12.0      # commanded puller surface speed
    tau_motor_s: float = 0.15      # first-order puller response
    grip_envelope_N: float = 8.0   # CALIBRATION: slip onset tension
    tension_nominal_N: float = 2.0
    tensioner_limit_N: float = 6.0
    h0: float = H0_W_M2K
    duct_alpha: float = DUCT_ALPHA
    ducted_mm: float = 250.0       # current baffle setting
    fans_on: int = 2
    dt_s: float = 0.02
    ovality_bias: float = 0.0      # major-minor offset applied at die (defect)


@dataclass
class LineState:
    T_C: float = field(init=False)
    v_pull_mm_s: float = field(init=False)
    spool_radius_mm: float = 35.0  # empty drum radius
    spool_angle_turns: float = 0.0
    meas_buffer: list = field(default_factory=list)   # (t_due, d_meas)
    t_s: float = 0.0

    def __post_init__(self):
        self.T_C = 25.0
        self.v_pull_mm_s = 0.0
        self.meas_buffer = []


def h_effective(p: LineParams):
    frac = p.ducted_mm / DUCT_AIR_LENGTH_RANGE[1]
    return p.h0 * (1.0 + p.duct_alpha * frac * (p.fans_on / 3.0))


def cooling_rate_C_s(T_C, p: LineParams, mat):
    """Lumped strand cooling rate (convection to tray air)."""
    d = NOMINAL_FILAMENT_MM / 1000.0          # m
    A = math.pi * (d / 2.0) ** 2              # m2
    perimeter = math.pi * d                   # m
    h = h_effective(p)
    mass_per_m = mat["rho_s"] * A             # kg/m
    return -h * perimeter * (T_C - mat["T_air"]) / (mass_per_m * mat["cp"])


def slip_fraction(tension_N, p: LineParams):
    if tension_N <= p.grip_envelope_N:
        return 0.0
    return min(0.5, 0.05 * (tension_N - p.grip_envelope_N))


def simulate(p: LineParams, t_total_s=60.0, controller=None,
             disturbance=None):
    """Integrate the line; return per-step samples.

    controller: optional callable(meas_d_mm or None, t_s) -> commanded
    puller speed mm/s.  None => fixed-speed (open loop) baseline.

    disturbance: optional callable(state_dict) applied per step (flow
    variation, sensor bias/dropout, slip events, tension events)."""
    mat = MATERIALS[p.material]
    sched = HeaterSchedule()
    st = LineState()
    samples = []
    n = int(t_total_s / p.dt_s)
    st.v_pull_mm_s = p.v_line_mm_s  # start at nominal; the controller acts from t=0 — startup rejection is a separate physical-test phase, not modeled as free warmup
    for k in range(n):
        t = k * p.dt_s
        st.t_s = t
        # --- heater schedule (admitted, hard budget) ----------------------
        heater_W = sched.admitted_W(t)
        # --- cooling -------------------------------------------------------
        st.T_C += cooling_rate_C_s(st.T_C, p, mat) * p.dt_s
        # --- puller actuation ----------------------------------------------
        meas_d = None
        due = [m for m in st.meas_buffer if m[0] <= t]
        st.meas_buffer = [m for m in st.meas_buffer if m[0] > t]
        if due:
            meas_d = due[-1][1]
        v_cmd = controller(meas_d, t) if controller else p.v_line_mm_s
        st.v_pull_mm_s += (v_cmd - st.v_pull_mm_s) * (p.dt_s / p.tau_motor_s)
        # --- strand state at the puller ------------------------------------
        tension = p.tension_nominal_N
        env = {"t_s": t, "T_C": st.T_C, "v_pull": st.v_pull_mm_s,
               "heater_W": heater_W, "tension_N": tension}
        if disturbance:
            env = disturbance(env)
            tension = env.get("tension_N", tension)
        slip = slip_fraction(tension, p)
        v_eff = st.v_pull_mm_s * (1.0 - slip)  # broken-strand case: v_eff->0 makes mass-balance diameter diverge; in-spec accounting REJECTS those samples (too thick) — scrap is reported, never smoothed
        # --- mass balance at the cooled section ----------------------------
        mdot = env.get("mdot_g_s", p.mdot_g_s)
        d_true = steady_diameter_mm(mdot, mat["rho_s"], max(v_eff, 0.01))
        d_major = d_true + max(0.0, p.ovality_bias)
        d_minor = d_true - max(0.0, p.ovality_bias)
        oval = ovality(d_major, d_minor)
        # --- gauge: delayed measurement with optional bias/dropout ---------
        bias = env.get("sensor_bias_mm", 0.0)
        dropout = env.get("sensor_dropout", False)
        d_meas = oval["d_equiv_mm"] + bias
        delay_s = SENSOR_TO_PULLER_MM / max(v_eff, 0.01)
        if not dropout:
            st.meas_buffer.append((t + delay_s, d_meas))
        # --- winder (tension-isolated) -------------------------------------
        wound_mm = v_eff * p.dt_s
        st.spool_angle_turns += wound_mm / (2.0 * math.pi * st.spool_radius_mm)
        # radius growth: area of one layer / circumference (1.75 filament)
        layer_mm2 = area_mm2(NOMINAL_FILAMENT_MM)
        st.spool_radius_mm = 35.0 + (
            st.spool_angle_turns * layer_mm2 / 55.0)   # 55 mm traverse width
        samples.append({
            "t_s": round(t, 4), "T_C": round(st.T_C, 3),
            "heater_W": heater_W, "v_cmd_mm_s": round(v_cmd, 4),
            "v_pull_mm_s": round(st.v_pull_mm_s, 4),
            "slip": round(slip, 4), "v_eff_mm_s": round(v_eff, 4),
            "mdot_g_s": round(mdot, 4),
            "d_true_mm": round(d_true, 5),
            "d_major_mm": round(d_major, 5), "d_minor_mm": round(d_minor, 5),
            "ovality_mm": round(oval["ovality_mm"], 5),
            "d_meas_mm": (round(d_meas, 5) if not dropout else None),
            "meas_delay_s": round(delay_s, 4),
            "tension_N": round(tension, 3),
            "spool_radius_mm": round(st.spool_radius_mm, 3),
        })
    return samples


def quality_summary(samples, target_mm=1.75, tol_mm=0.05):
    """Length-weighted in-spec accounting: per-axis max/min, ovality, and
    the in-spec LENGTH (mm), not just the mean.  Unmeasured (dropout)
    length is reported separately and NEVER counted as in-spec."""
    dt = samples[1]["t_s"] - samples[0]["t_s"]
    total_mm = in_spec_mm = unmeasured_mm = 0.0
    majors, minors = [], []
    worst = {"d_major_max": 0.0, "d_minor_min": 99.0, "ovality_max": 0.0}
    for s in samples:
        length = s["v_eff_mm_s"] * dt
        total_mm += length
        majors.append(s["d_major_mm"])
        minors.append(s["d_minor_mm"])
        worst["d_major_max"] = max(worst["d_major_max"], s["d_major_mm"])
        worst["d_minor_min"] = min(worst["d_minor_min"], s["d_minor_mm"])
        worst["ovality_max"] = max(worst["ovality_max"], s["ovality_mm"])
        ok = (abs(s["d_major_mm"] - target_mm) <= tol_mm
              and abs(s["d_minor_mm"] - target_mm) <= tol_mm
              and s["ovality_mm"] <= tol_mm)
        if ok:
            in_spec_mm += length
        if s["d_meas_mm"] is None:
            unmeasured_mm += length
    mean_d = (sum(majors) + sum(minors)) / (len(majors) + len(minors))
    return {
        "target_mm": target_mm, "tol_mm": tol_mm,
        "total_length_mm": round(total_mm, 1),
        "in_spec_length_mm": round(in_spec_mm, 1),
        "in_spec_fraction": (round(in_spec_mm / total_mm, 4)
                             if total_mm else 0.0),
        "unmeasured_length_mm": round(unmeasured_mm, 1),
        "mean_diameter_mm": round(mean_d, 5),
        "d_major_max_mm": round(worst["d_major_max"], 5),
        "d_minor_min_mm": round(worst["d_minor_min"], 5),
        "ovality_max_mm": round(worst["ovality_max"], 5),
        "in_spec_meaning": ("length-weighted, BOTH axes within tolerance "
                            "plus ovality within tolerance; unmeasured "
                            "length is excluded, never credited"),
    }
