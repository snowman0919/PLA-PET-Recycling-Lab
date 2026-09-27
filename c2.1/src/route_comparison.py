"""Same-hardware fixed-speed vs measured-diameter feedback screening.

An extra reheated forming pass has no calibrated pressure/flow/temperature or
geometry model and cannot be assigned a fictitious diameter gain. It remains
an explicit unranked alternative until a real test and costing exist.
"""
from __future__ import annotations

import ctypes
import json
from pathlib import Path

import process_model as pm
from build_firmware import library_for_source

_native_pi = None
_native_library = None


def native_pi():
    global _native_pi, _native_library
    if _native_pi is None:
        _native_library = ctypes.CDLL(str(library_for_source()))
        function = _native_library.ppr_diameter_pi_step
        function.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double,
                             ctypes.POINTER(ctypes.c_double),
                             ctypes.POINTER(ctypes.c_double)]
        function.restype = ctypes.c_double
        _native_pi = function
    return _native_pi



HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
TARGET_MM = 1.75
TOL_MM = 0.05


def fixed_speed_controller(p):
    return lambda measured_mm, t_s, gauge_invalid=False: p.v_line_mm_s


class PIController:
    """Host model runs the C++ controller's PI kernel, not a Python replica.

    The C++ controller latches quality_hold immediately on an explicitly
    invalid axis after feedback is armed, or after a stale valid reading.
    This parcel model uses >1s without a new sample for the latter case.
    It does not emulate the entire safety allocator.
    """
    def __init__(self, v_nominal):
        self.v_nominal = v_nominal
        self.integral = ctypes.c_double(0.0)
        self.command = ctypes.c_double(v_nominal)
        self.last_time = None
        self.halted_at_s = None

    def __call__(self, measured_mm, t_s, gauge_invalid=False):
        if self.halted_at_s is not None:
            return 0.0
        if gauge_invalid and self.last_time is not None:
            self.halted_at_s = t_s
            return 0.0
        if measured_mm is None:
            if self.last_time is not None and t_s - self.last_time > 1.0:
                self.halted_at_s = t_s
                return 0.0
            return self.command.value
        dt = 0.0 if self.last_time is None else max(0.0, t_s - self.last_time)
        self.last_time = t_s
        return native_pi()(self.v_nominal, measured_mm, dt,
                           ctypes.byref(self.integral),
                           ctypes.byref(self.command))


def disturbance_script(step):
    t = step["t_s"]
    env = clutch_fault_script(step)
    if 75 <= t < 90:
        env["mdot_factor"] = 1.35
    if 110 <= t < 125:
        env["mdot_factor"] = 0.71
    if 45 <= t < 155:
        env["sensor_bias_mm"] = 0.015  # uncalibrated sensor offset
    if 145 <= t < 153:
        env["sensor_dropout"] = True
    if 90 <= t < 110:
        env["ambient_shift_C"] = 8.0
        env["barrel_loss_extra_W"] = 25.0
    return env

def minor_axis_dropout_script(step):
    """Fault only one orthogonal gauge axis after feedback is armed."""
    env = dict(step)
    if 145 <= step["t_s"] < 153:
        env["sensor_minor_dropout"] = True
    return env


def sustained_offset_script(step):
    return {**step, "mdot_factor": 1.2}


def clutch_fault_script(step):
    """Apply the same assumed winding-clutch fault in either scenario."""
    env = dict(step)
    if 170 <= step["t_s"] < 178:
        env["clutch_failed"] = True
        env["tension_N"] = 10.0  # fault injection; working clutch caps at 6 N
    return env


def run_route(name, controller_factory, scenario="transient", **overrides):
    p = pm.LineParams(material="PLA", **overrides)
    controller = controller_factory(p)
    script = {"transient": disturbance_script,
              "sustained_offset": sustained_offset_script,
              "clutch_fault": clutch_fault_script,
              "minor_axis_dropout": minor_axis_dropout_script,
              "nominal": None}[scenario]
    duration = 240.0 if scenario != "nominal" else 90.0
    samples, pending = pm.simulate(
        p, t_total_s=duration, controller=controller, disturbance=script,
        return_pending=True)
    summary = pm.quality_summary(samples, TARGET_MM, TOL_MM)
    summary.update(route=name, scenario=scenario, samples=len(samples),
                   controller_halted_at_s=getattr(controller, "halted_at_s", None),
                   requested_duration_s=duration,
                   nominal_mdot_g_h=round(p.mdot_g_s * 3600, 2),
                   nominal_speed_mm_s=round(p.v_line_mm_s, 4),
                   pending_unqualified_length_mm=round(pending, 2),
                   produced_length_mm=round(summary["total_length_mm"] + pending, 2),
                   qualified_fraction_of_produced=round(
                       summary["in_spec_length_mm"] /
                       (summary["total_length_mm"] + pending), 4),
                   die_to_gauge_mm=pm.GAUGE_X - pm.DIE_EXIT_X,
                   gauge_to_nip_mm=pm.PULLER_NIP_X - pm.GAUGE_X,
                   max_admitted_heater_W=max((s["heater_W"] for s in samples),
                                              default=0.0),
                   max_barrel_C=max((s["barrel_C"] for s in samples),
                                    default=None),
                   maximum_nip_center_C=max((s["core_C"] for s in samples),
                                            default=None))
    return summary, samples


def thermal_case(material, fans):
    p = pm.LineParams(material=material, fans_on=fans)
    profile = pm.cooling_profile(p, p.v_line_mm_s)
    return {
        "material": material, "fans_on": fans,
        "reference_mdot_g_h": pm.NOMINAL_MDOT_G_S * 3600,
        "reference_speed_mm_s": round(p.v_line_mm_s, 3),
        "gauge_core_C": round(profile["gauge_core_C"], 2),
        "gauge_ready": profile["gauge_ready"],
        "thermal_only_speed_limit_mm_s": round(pm.max_cooling_speed_mm_s(p), 2),
        "status": "UNCALIBRATED_CONVECTION_AND_MATERIAL_ESTIMATE",
    }


def compare():
    results = []
    traces = {}
    for scenario in ("nominal", "transient", "sustained_offset",
                     "clutch_fault", "minor_axis_dropout"):
        for name, factory in (("C_fixed_speed", fixed_speed_controller),
                              ("A_diameter_feedback",
                               lambda p: PIController(p.v_line_mm_s))):
            summary, samples = run_route(name, factory, scenario)
            results.append(summary)
            traces[f"{scenario}/{name}"] = [
                {key: s[key] for key in ("t_s", "t_created_s",
                    "d_major_mm", "d_minor_mm", "d_true_mm",
                    "d_meas_major_mm", "d_meas_minor_mm", "d_meas_mm",
                    "core_C", "barrel_birth_C", "barrel_C", "v_cmd_mm_s",
                    "birth_speed_mm_s", "die_to_gauge_delay_s",
                    "gauge_to_nip_delay_s")}
                for s in samples[::max(1, len(samples) // 12)]]
    verdict = {
        "model": "UNCALIBRATED_2_NODE_STRAND_AND_HEATER_SENSITIVITY",
        "routes": results,
        "sample_traces": traces,
        "thermal_screen": [thermal_case(material, fans)
                           for material in pm.MATERIALS for fans in (2, 3)],
        "forming_pass": {
            "status": "UNRANKED_NO_PHYSICAL_FORMING_MODEL_OR_COST",
            "in_spec_fraction": None,
            "reason": "No calibrated melt pressure, reheat, draw/shape mechanism, thermal history or additional power/cost estimate; bore diameter cannot repair underfill or bubbles.",
        },
        "limitations": [
            "Reference-feed 100 g/h is a design target; screw throughput unmeasured.",
            "Solid density, conductivity, convection, grip, clutch and temperature-flow sensitivity are assumed, not measured on PPR.",
            "Spool torque/radius gives quasistatic tension only; the lighter CAD drum does not validate acceleration, inertia, welds, bearing load or clutch transient torque.",
            "The puller's influence on the molten draw point is instantaneous here; strand elasticity, melt swelling, pressure and contact deformation are omitted.",
            "PI arithmetic uses the host-built C++ firmware kernel; a >1s post-start absence of new gauge samples or an explicitly invalid axis after arming stops this model. Other firmware safety, power and motor I/O are NOT exercised in the parcel simulation.",
            "The composite transient's clutch fault at 170..178 s occurs after the feedback route halts on missing gauge at 146 s; the isolated clutch_fault scenario exposes both routes to that fault without bypassing the HOLD.",
            "Fixed-speed baseline uses the same diagnostic gauge for after-the-fact scoring, not as a live motor interlock.",
            "The modeled nip quality gate checks both true axes and both biased gauge axes; an invalid axis immediately halts armed feedback, while a short absence of new samples does not. The PI arithmetic uses their area-equivalent diameter, matching the C++ reference controller but not proving physical calibration.",
            "Two-axis sensor accuracy and native continuous production remain unverified.",
            "In-spec fractions are scenario sensitivity, not physical yield or economic acceptance.",
        ],
    }
    output = ROOT / "results/downstream_route_comparison.json"
    output.write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps([{"scenario": r["scenario"], "route": r["route"],
                       "in_spec_fraction": r["in_spec_fraction"],
                       "unmeasured_length_mm": r["unmeasured_length_mm"],
                       "thermally_unready_length_mm": r["thermally_unready_length_mm"]}
                      for r in results], indent=2))
    return verdict


if __name__ == "__main__":
    compare()
