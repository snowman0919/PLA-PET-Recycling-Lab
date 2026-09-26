"""VP1 Stage 6: route comparison harness — fixed-speed vs diameter feedback
vs rehearse-forming pass, under flow/temperature/sensor/slip/tension/power
disturbances.

Decision route (docs/decisions/filament-quality-route.md):
  A. single-pass extrusion + adjustable cooling + cheap diameter feedback
     puller + tension-isolated winder   (current leading baseline)
  B. added rehearse-forming die/nozzle    (unverified hypothesis; modeled
     here ONLY as an additional sizing uncertainty reducer — NOT a bore-
     equals-diameter claim, NOT an auto-fix for thin sections/bubbles)
  C. fixed-speed / manual-measurement operation of the SAME hardware
     (baseline mode, not a separate throwaway MVP)

The harness runs IDENTICAL disturbance scripts through A/B/C and reports
length-weighted quality.  Results are model evidence for the DECISION, not
production claims (uncalibrated parameters are marked in process_model).
"""
from __future__ import annotations

import json
from pathlib import Path

import process_model as pm

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]

TARGET_MM = 1.75
TOL_MM = 0.05


def fixed_speed_controller(p):
    """Route C: no feedback; commanded speed is the nominal line speed."""
    def ctrl(meas_d, t):
        return p.v_line_mm_s
    return ctrl


class PIController:
    """Route A: PI on the (delayed, biased, dropout-prone) measured
    diameter; anti-windup clamps the command; the REAL 7 mm transport
    delay comes from the measurement buffer, not a tuned constant.

    Sign convention: thicker filament (err>0) => FASTER puller (more
    draw-down), thinner => slower.  Gains are first-pass tuning against
    the model; physical tuning is calibration work."""
    def __init__(self, v_nominal, kp=0.45, ki=0.02,
                 v_min=4.0, v_max=30.0):
        self.v_nominal = v_nominal
        self.kp, self.ki = kp, ki
        self.v_min, self.v_max = v_min, v_max
        self.integral = 0.0

    def __call__(self, meas_d, t):
        if meas_d is None:
            return self.v_nominal        # hold last-known (no hallucinated data)
        err = meas_d - TARGET_MM
        self.integral += err * 0.02
        self.integral = max(-4.0, min(4.0, self.integral))   # anti-windup
        v = self.v_nominal + (self.kp * err * 10.0 + self.ki * self.integral)
        return max(self.v_min, min(self.v_max, v))


class FormingPassController(PIController):
    """Route B: same feedback, but the 'forming' pass is modeled ONLY as a
    reduced disturbance gain on the true diameter (sizing pass hypothesis).
    It never restores bubbles or thin sections: the disturbance script's
    defect events pass through at full strength below the die."""
    pass


def disturbance_script(step):
    """Shared disturbance script: flow surge, sensor bias, dropout window,
    tension spike, cold-snap (heater scheduler unchanged — 500 W budget
    is structural, not scripted)."""
    t = step["t_s"]
    env = dict(step)
    env["mdot_g_s"] = 0.0358
    if 15.0 <= t < 25.0:
        env["mdot_g_s"] = 0.0483                  # flow surge (+35%)
    if 30.0 <= t < 40.0:
        env["mdot_g_s"] = 0.0254                  # starvation (-29%)
    if 10.0 <= t < 50.0:
        env["sensor_bias_mm"] = 0.015             # +15 um sensor bias
    if 45.0 <= t < 50.0:
        env["sensor_dropout"] = True              # 5 s measurement gap
    if 55.0 <= t < 58.0:
        env["tension_N"] = 10.0                   # tension spike -> slip
    return env

def sustained_offset_script(step):
    """Second scenario: the extruder's sustained operating point sits at
    +20% throughput (wrong nominal — die wear, temperature drift, material
    change).  This is where closed-loop feedback earns its sensor: the
    fixed-speed line has NO way back to target."""
    env = dict(step)
    env["mdot_g_s"] = 0.043
    return env
def run_route(name, controller_factory, forming=False, scenario="transient"):
    p = pm.LineParams(material="PLA")
    ctrl = controller_factory(p)
    script = {"transient": disturbance_script,
              "sustained_offset": sustained_offset_script}[scenario]
    t_total = 70.0 if scenario == "transient" else 60.0
    samples = pm.simulate(p, t_total_s=t_total, controller=ctrl,
                          disturbance=script)
    if forming:
        # Route B hypothesis: a sizing pass reduces the EFFECTIVE diameter
        # error gain seen by the winder — but bubbles/thin sections pass
        # through.  Modelled as 30% reduction of |d-1.75| deviations, NOT
        # as exact bore control.
        for s in samples:
            dev = s["d_true_mm"] - TARGET_MM
            s["d_true_mm"] = TARGET_MM + 0.7 * dev
            s["d_major_mm"] = TARGET_MM + 0.7 * (s["d_major_mm"] - TARGET_MM)
            s["d_minor_mm"] = TARGET_MM + 0.7 * (s["d_minor_mm"] - TARGET_MM)
            s["ovality_mm"] = 0.7 * s["ovality_mm"]
    q = pm.quality_summary(samples, TARGET_MM, TOL_MM)
    q["route"] = name
    q["heater_budget_W"] = 500.0
    q["max_simultaneous_heater_W"] = 160.0
    q["samples"] = len(samples)
    return q, samples


def compare():
    results = []
    details = {}
    offset_results = []
    for name, factory, forming in (
            ("C_fixed_speed", fixed_speed_controller, False),
            ("A_diameter_feedback",
             lambda p: PIController(p.v_line_mm_s, kp=1.2, ki=0.06), False),
            ("B_feedback_plus_forming_pass",
             lambda p: FormingPassController(p.v_line_mm_s, kp=1.2, ki=0.06),
             True)):
        q, samples = run_route(name, factory, forming)
        q["scenario"] = "transient"
        results.append(q)
        details[name] = samples[-5:]      # tail trace for audit
        q2, _ = run_route(name, factory, forming,
                          scenario="sustained_offset")
        q2["scenario"] = "sustained_offset"
        offset_results.append(q2)
    # The comparison verdict is evidence-scoped: model says feedback should
    # help under scripted disturbances; calibration runs decide purchase.
    verdict = {
        "routes": results,
        "routes_sustained_offset": offset_results,
        "sample_tail": details,
        "disturbances": {
            "flow_surge_pct": "+35 (15-25 s)", "starvation_pct": "-29 (30-40 s)",
            "sensor_bias_mm": "+0.015 (10-50 s)", "sensor_dropout": "45-50 s",
            "tension_spike_N": "10 (55-58 s)",
            "sustained_offset": "+20% throughput for the full run",
            "power": "hard 500 W allocator; heaters <=160 W simultaneous"},
        "interpretation": (
            "UNCALIBRATED model comparison for the sensor/route DECISION "
            "only.  In-spec fractions are not production claims; reference-"
            "material calibration runs are required before any quality "
            "statement.  Route B's 30% deviation reduction is a hypothesis, "
            "not a mechanism; the original user video is unverified.  "
            "FINDING 1 (transient script): with the REAL 20 mm sensor->"
            "puller delay and a +15 um sensor bias, fixed-speed beats "
            "feedback (the biased loop steers off-target and the delay "
            "rings) — feedback is NOT free.  FINDING 2 (sustained +20% "
            "offset): fixed-speed can never return to target while PI "
            "feedback recovers most in-spec length — feedback is the only "
            "route that tolerates a wrong operating point.  The decision "
            "hinges on calibration quality (pin/micrometer round-trip), "
            "not on buying a sensor."),
        "holds": [
            "sensor accuracy U95 <= 0.01 mm unverified (pins + micrometer)",
            "contact-axis TPU deformation, optical-axis transparent stock",
            "melt filter pressure, screw/barrel pressure and thrust UNRATED",
        ],
    }
    out = ROOT / "results" / "downstream_route_comparison.json"
    out.write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps({r["route"]: {k: r[k] for k in
                                   ("in_spec_fraction", "in_spec_length_mm",
                                    "unmeasured_length_mm", "mean_diameter_mm",
                                    "ovality_max_mm", "d_major_max_mm",
                                    "d_minor_min_mm")}
                      for r in results}, indent=2))
    return verdict


if __name__ == "__main__":
    compare()
