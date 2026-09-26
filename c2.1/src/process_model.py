"""Reference-feedstock downstream screening model (not a production qualification).

Each die-exit strand element carries its own area, length, temperature and
measurement status through die -> gauge -> nip. Puller speed is assumed to
propagate through the molten draw zone without elastic delay; neither screw
pressure nor melt rheology is calibrated. The die-to-gauge residence time,
not gauge-to-nip distance, is the feedback dead time. Thermal parameters are
explicit sensitivity assumptions; physical temperatures and gauge accuracy
must be measured before accepting any in-spec prediction.
"""
from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path

DIE_EXIT_X = 540.0
TRAY_START_X = 545.0
GAUGE_X = 809.0
PULLER_NIP_X = 829.0
TRAY_END_X = 820.0
NOMINAL_FILAMENT_MM = 1.75
DESIGN = json.loads((Path(__file__).resolve().parents[2] /
                     "design/parameters.json").read_text())
NOMINAL_MDOT_G_S = DESIGN["extruder"]["nominal_target_g_h"] / 3600.0

# Planning inputs, not material certificates; PET means PET, not PETG.
# k is the assumed solid thermal conductivity. T_ready is a conservative
# assumed center-temperature gate for contact with the gauge/nip.
MATERIALS = {
    "PLA": dict(rho_s=1240.0, cp=1800.0, k=0.20, T_die=185.0,
                T_ready=55.0, T_air=35.0),
    "PET": dict(rho_s=1330.0, cp=1250.0, k=0.20, T_die=255.0,
                T_ready=60.0, T_air=35.0),
    "TPU": dict(rho_s=1210.0, cp=1900.0, k=0.18, T_die=215.0,
                T_ready=50.0, T_air=35.0),
}


def area_mm2(d_mm):
    return math.pi * d_mm * d_mm / 4.0


def nominal_speed_mm_s(material="PLA", mdot_g_s=NOMINAL_MDOT_G_S):
    return mdot_g_s * 1e6 / (MATERIALS[material]["rho_s"] * area_mm2(1.75))


def steady_diameter_mm(mdot_g_s, rho_s_kg_m3, v_line_mm_s):
    if mdot_g_s <= 0 or rho_s_kg_m3 <= 0 or v_line_mm_s <= 0:
        raise ValueError("mass flow, solid density and line speed must be positive")
    return math.sqrt(4.0e6 * mdot_g_s / (math.pi * rho_s_kg_m3 * v_line_mm_s))


def ovality(d_major_mm, d_minor_mm):
    return {"d_equiv_mm": math.sqrt(d_major_mm * d_minor_mm),
            "ovality_mm": d_major_mm - d_minor_mm,
            "ovality_ratio": d_major_mm / d_minor_mm}


@dataclass
class LineParams:
    material: str = "PLA"
    mdot_g_s: float = NOMINAL_MDOT_G_S
    v_line_mm_s: float | None = None
    dt_s: float = 0.1
    tau_motor_s: float = 0.5
    ducted_mm: float = 250.0  # length starting at x545, not a global multiplier
    fans_on: int = 3
    h0_W_m2K: float = 25.0  # ASSUMED natural/weak convection
    duct_alpha: float = 3.0  # ASSUMED forced enhancement at 3 fans
    spool_core_radius_mm: float = 35.0
    spool_width_mm: float = 55.0
    spool_fill_fraction: float = 0.8
    clutch_torque_Nmm: float = 70.0  # ASSUMED; ~2 N at empty spool
    tensioner_limit_N: float = 6.0
    grip_envelope_N: float = 8.0
    ovality_bias_mm: float = 0.0  # half difference; area remains mass-conserving
    heater_slot_s: float = 30.0  # matches controller_core.cpp; switching device unselected
    barrel_heat_capacity_J_K: float = 180.0  # per third, steel+polymer estimate
    barrel_loss_W_K: float = 0.10  # per zone, insulation-dependent
    die_heat_capacity_J_K: float = 90.0
    die_loss_W_K: float = 0.15
    ambient_C: float = 25.0
    flow_temp_sensitivity_per_C: float = 0.005  # ASSUMED; varies with screw/pressure

    def __post_init__(self):
        if self.material not in MATERIALS:
            raise ValueError(f"unsupported material: {self.material}")
        if self.v_line_mm_s is None:
            self.v_line_mm_s = nominal_speed_mm_s(self.material, self.mdot_g_s)
        if (self.dt_s <= 0 or self.v_line_mm_s <= 0 or self.mdot_g_s <= 0
                or self.tau_motor_s < self.dt_s or not 0 <= self.ducted_mm <= 275
                or not 0 <= self.fans_on <= 3 or self.heater_slot_s < self.dt_s
                or self.spool_fill_fraction <= 0):
            raise ValueError("invalid process geometry, power or time step")


@dataclass
class Element:
    birth_s: float
    birth_distance_mm: float
    length_mm: float
    d_major_mm: float
    d_minor_mm: float
    core_C: float
    skin_C: float
    gauge_s: float | None = None
    measured_mm: float | None = None
    gauge_ready: bool = False
    ready_x_mm: float | None = None
    source_mdot_g_s: float = 0.0
    birth_speed_mm_s: float = 0.0
    barrel_birth_C: float = 0.0


def h_effective(p: LineParams, x_mm=TRAY_START_X):
    """Air coefficient at position; only the ducted section gets fan credit."""
    if TRAY_START_X <= x_mm < min(TRAY_END_X, TRAY_START_X + p.ducted_mm):
        return p.h0_W_m2K * (1 + p.duct_alpha * p.fans_on / 3)
    return p.h0_W_m2K


def cooling_rate_C_s(T_C, p: LineParams, mat):
    """Lumped reference rate for comparisons; simulation uses two radial nodes."""
    return (-4 * h_effective(p) * (T_C - mat["T_air"])
            / (mat["rho_s"] * mat["cp"] * NOMINAL_FILAMENT_MM / 1000))


def cool_element(e: Element, p: LineParams, mat: dict, x_mm: float,
                 air_C: float):
    """Core (r<r/2) ↔ outer annulus ↔ air, per unit strand length.

    Cylindrical resistance ln(2)/(2πk) is an approximate radial partition,
    not a CFD solution. Apply convection only at x>=545; ambient applies
    outside the tray. Explicit step is stable for the stated dt and radii.
    """
    d_m = math.sqrt(e.d_major_mm * e.d_minor_mm) / 1000
    heat_capacity = mat["rho_s"] * mat["cp"] * math.pi * d_m * d_m / 4
    conductance = 2 * math.pi * mat["k"] / math.log(2)
    convection = math.pi * d_m * h_effective(p, x_mm)
    transfer = conductance * (e.core_C - e.skin_C)
    e.core_C -= p.dt_s * transfer / (0.25 * heat_capacity)
    e.skin_C += p.dt_s * (transfer - convection * (e.skin_C - air_C)) / (0.75 * heat_capacity)
    if e.ready_x_mm is None and e.core_C <= mat["T_ready"]:
        e.ready_x_mm = x_mm


def cooling_profile(p: LineParams, speed_mm_s: float):
    """Steady 1.75mm reference strand at a specified line speed.

    Thermal-only calculation; matching mass flow would have to be supplied
    by an as-yet unqualified screw. The gauge is the readiness constraint.
    """
    if speed_mm_s <= 0:
        raise ValueError("line speed must be positive")
    mat = MATERIALS[p.material]
    e = Element(0.0, 0.0, 0.0, NOMINAL_FILAMENT_MM,
                NOMINAL_FILAMENT_MM, mat["T_die"], mat["T_die"])
    gauge_core = gauge_skin = None
    steps = math.ceil((PULLER_NIP_X - DIE_EXIT_X) / (speed_mm_s * p.dt_s))
    for step in range(steps + 1):
        x = DIE_EXIT_X + step * speed_mm_s * p.dt_s
        cool_element(e, p, mat, x, mat["T_air"])
        if gauge_core is None and x >= GAUGE_X:
            gauge_core, gauge_skin = e.core_C, e.skin_C
    return {"gauge_core_C": gauge_core, "gauge_skin_C": gauge_skin,
            "nip_core_C": e.core_C, "nip_skin_C": e.skin_C,
            "first_ready_x_mm": e.ready_x_mm,
            "gauge_ready": gauge_core <= mat["T_ready"]}


def max_cooling_speed_mm_s(p: LineParams):
    """Upper thermal-only speed at which the *gauge* sees a ready core.

    The bounded search returns 0 if even 0.5mm/s is insufficient; a
    value of 40 denotes a search boundary, not proven hardware capacity.
    """
    lower, upper = 0.5, 40.0
    if not cooling_profile(p, lower)["gauge_ready"]:
        return 0.0
    if cooling_profile(p, upper)["gauge_ready"]:
        return upper
    for _ in range(20):
        mid = (lower + upper) / 2
        if cooling_profile(p, mid)["gauge_ready"]:
            lower = mid
        else:
            upper = mid
    return lower


def slip_fraction(tension_N, p: LineParams):
    return min(0.5, max(0.0, tension_N - p.grip_envelope_N) * 0.05)


def heater_step(temperatures_C: list[float], p: LineParams, t_s: float,
                mat: dict, mdot_g_s: float, loss_extra_W: float = 0.0):
    """3 thermostatic 100 W barrel bands; at most one on in each slot.

    The 60 W die cartridge has its own thermostat. Start from preheated
    setpoints; qualification warmup, sensor faults and thermal fuses are not
    emulated. Available power is the admitted load, not requested load.
    """
    setpoints = (mat["T_die"] - 30, mat["T_die"] - 15,
                 mat["T_die"], mat["T_die"])
    first = int(t_s / p.heater_slot_s) % 3
    selected = next((idx for idx in ((first + k) % 3 for k in range(3))
                     if temperatures_C[idx] < setpoints[idx] + 0.25), None)
    watts = [0.0, 0.0, 0.0, 0.0]
    if selected is not None:
        watts[selected] = 100.0
    if temperatures_C[3] < setpoints[3] + 0.25:
        watts[3] = 60.0
    for idx in range(4):
        loss = p.barrel_loss_W_K if idx < 3 else p.die_loss_W_K
        capacity = (p.barrel_heat_capacity_J_K if idx < 3
                    else p.die_heat_capacity_J_K)
        inlet_C = p.ambient_C if idx == 0 else setpoints[idx - 1]
        polymer_W = (mdot_g_s / 1000 * mat["cp"] *
                     max(0.0, setpoints[idx] - inlet_C))
        temperatures_C[idx] += p.dt_s * (
            watts[idx] - loss * (temperatures_C[idx] - p.ambient_C)
            - polymer_W - loss_extra_W / 4) / capacity
    return watts


def simulate(p: LineParams, t_total_s=180.0, controller=None,
             disturbance=None, return_pending=False):
    """Return elements at the nip, including residence/quality trace.

    Disturbance callable receives {t_s, heater_W, barrel_C, spool_radius_mm,
    tension_N, v_pull}; can return mdot_factor, ambient_shift_C,
    sensor_bias_mm, sensor_dropout, clutch_failed, tension_N and
    barrel_loss_extra_W. Unmeasured/uncooled elements are NEVER credited.
    """
    mat = MATERIALS[p.material]
    barrel = [mat["T_die"] - 30, mat["T_die"] - 15,
              mat["T_die"], mat["T_die"]]
    elements = deque()
    samples = []
    distance_mm = wound_mm = 0.0
    v_surface = p.v_line_mm_s
    measured = None
    loss_extra_W = 0.0
    last_mdot = p.mdot_g_s
    n = int(t_total_s / p.dt_s)
    for k in range(n):
        t = k * p.dt_s
        watts = heater_step(barrel, p, t, mat, last_mdot, loss_extra_W)
        radius = math.sqrt(p.spool_core_radius_mm ** 2 +
                           area_mm2(NOMINAL_FILAMENT_MM) * wound_mm /
                           (math.pi * p.spool_width_mm * p.spool_fill_fraction))
        env = {"t_s": t, "heater_W": sum(watts), "barrel_C": barrel[2],
               "spool_radius_mm": radius, "v_pull": v_surface,
               "tension_N": min(p.clutch_torque_Nmm / radius, p.tensioner_limit_N)}
        if disturbance:
            env = disturbance(env)
        loss_extra_W = env.get("barrel_loss_extra_W", 0.0)
        tension = env.get("tension_N", 0.0)
        if not env.get("clutch_failed", False):
            tension = min(tension, p.clutch_torque_Nmm / radius,
                          p.tensioner_limit_N)
        v_cmd = controller(measured, t) if controller else p.v_line_mm_s
        if getattr(controller, "halted_at_s", None) is not None:
            # A latched gauge loss stops the process. The strand still between
            # die and nip cannot be credited without a restart/purge.
            break
        measured = None  # one fresh gauge observation per element, not a held echo
        v_surface += (v_cmd - v_surface) * min(1.0, p.dt_s / p.tau_motor_s)
        slip = slip_fraction(tension, p)
        v_eff = v_surface * (1 - slip)
        distance_mm += v_eff * p.dt_s
        wound_mm += v_eff * p.dt_s
        # Mass conservation at the assumed instantaneous draw point. Temperature
        # influence is an uncalibrated flow sensitivity; no hidden throughput gain.
        base_flow = p.mdot_g_s * env.get("mdot_factor", 1.0)
        mdot = base_flow * max(0.05, 1 + p.flow_temp_sensitivity_per_C *
                               (barrel[2] - mat["T_die"]))
        last_mdot = mdot
        d_eq = steady_diameter_mm(mdot, mat["rho_s"], max(v_eff, 0.01))
        bias = p.ovality_bias_mm
        major = math.sqrt(d_eq * d_eq + bias * bias) + bias
        minor = math.sqrt(d_eq * d_eq + bias * bias) - bias
        elements.append(Element(t, distance_mm, v_eff * p.dt_s, major,
                                minor, barrel[3], barrel[3],
                                source_mdot_g_s=mdot, birth_speed_mm_s=v_eff,
                                barrel_birth_C=barrel[2]))
        air_C = mat["T_air"] + env.get("ambient_shift_C", 0.0)
        for e in elements:
            x = DIE_EXIT_X + distance_mm - e.birth_distance_mm
            cool_element(e, p, mat, x, air_C)
            if e.gauge_s is None and x >= GAUGE_X:
                e.gauge_s = t
                e.gauge_ready = e.core_C <= mat["T_ready"]
                if not env.get("sensor_dropout", False):
                    e.measured_mm = math.sqrt(e.d_major_mm * e.d_minor_mm) + env.get(
                        "sensor_bias_mm", 0.0)
                    measured = e.measured_mm
        while elements and DIE_EXIT_X + distance_mm - elements[0].birth_distance_mm >= PULLER_NIP_X:
            e = elements.popleft()
            ready = e.core_C <= mat["T_ready"] and e.gauge_ready
            samples.append({
                "t_s": t, "t_created_s": e.birth_s, "t_gauge_s": e.gauge_s,
                "die_to_gauge_delay_s": round(e.gauge_s - e.birth_s, 3),
                "gauge_to_nip_delay_s": round(t - e.gauge_s, 3),
                "length_mm": e.length_mm,
                "d_major_mm": e.d_major_mm, "d_minor_mm": e.d_minor_mm,
                "d_true_mm": math.sqrt(e.d_major_mm * e.d_minor_mm),
                "ovality_mm": e.d_major_mm - e.d_minor_mm,
                "d_meas_mm": e.measured_mm,
                "core_C": e.core_C, "skin_C": e.skin_C,
                "ready_x_mm": e.ready_x_mm, "thermal_ready": ready,
                "heater_W": sum(watts), "barrel_C": barrel[2],
                "v_cmd_mm_s": v_cmd, "v_eff_mm_s": v_eff,
                "mdot_g_s": e.source_mdot_g_s, "slip": slip,
                "birth_speed_mm_s": e.birth_speed_mm_s,
                "barrel_birth_C": e.barrel_birth_C,
                "tension_N": tension, "spool_radius_mm": radius,
                "winder_rpm": 60 * v_eff / (2 * math.pi * radius),
            })
    if return_pending:
        return samples, sum(e.length_mm for e in elements)
    return samples


def quality_summary(samples, target_mm=1.75, tol_mm=0.05):
    """Length at nip; reject both missing gauge and thermally unready strand."""
    total = good = missing = unready = 0.0
    min_d, max_d, max_oval = math.inf, -math.inf, 0.0
    weighted_d = 0.0
    for s in samples:
        length = s["length_mm"]
        total += length
        major, minor = s["d_major_mm"], s["d_minor_mm"]
        min_d, max_d = min(min_d, minor), max(max_d, major)
        max_oval = max(max_oval, major - minor)
        weighted_d += length * (major + minor) / 2
        if s["d_meas_mm"] is None:
            missing += length
        if not s["thermal_ready"]:
            unready += length
        if (s["d_meas_mm"] is not None and s["thermal_ready"]
                and target_mm - tol_mm <= minor <= major <= target_mm + tol_mm
                and major - minor <= tol_mm):
            good += length
    return {
        "target_mm": target_mm, "tol_mm": tol_mm,
        "total_length_mm": round(total, 2),
        "in_spec_length_mm": round(good, 2),
        "in_spec_fraction": round(good / total, 4) if total else 0.0,
        "unmeasured_length_mm": round(missing, 2),
        "thermally_unready_length_mm": round(unready, 2),
        "mean_diameter_mm": round(weighted_d / total, 5) if total else None,
        "d_major_max_mm": round(max_d, 5) if total else None,
        "d_minor_min_mm": round(min_d, 5) if total else None,
        "ovality_max_mm": round(max_oval, 5),
        "in_spec_meaning": "modeled, measured, thermally ready nip length; not physical yield",
    }
