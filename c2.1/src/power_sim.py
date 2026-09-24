"""VP1 Stage 4: virtual duty-cycle power simulation over the nameplate table.

Reads the device table from c2.1/results/electrical_load.json (nameplate
values + evidence grades) and simulates the extruder heat-up -> shredding ->
steady filament production duty cycle at 1 s resolution, applying the staged
concurrency policy implemented in c2.1/firmware/controller_core.cpp:

- devices are admitted in priority order (fans -> EX-H60 -> M1 -> M2 ->
  auxiliary demand -> one rotating EX-H100 band);
- 500 W is the hard modeled operating budget: the next demand exceeding it
  is refused, including an over-budget band;
- 792 W (= 24 V x 33 A) is the separate PSU current-derived hardware
  maximum, not permission to operate above 500 W;
- at most ONE EX-H100 band at any instant (firmware structural invariant;
  the EL_CURRENT_LIMITER hardware interlock requirement stands anyway).

EVIDENCE GRADES (kept explicit per device, from electrical_load.json):
- NAMEPLATE_SOURCE: heater bands/cartridge (design/assembly.json part names).
- UNRATED_ESTIMATE: M1/M2 (not-owned references; nameplate current x 24 V)
  and the 9RA0824H1001 fans (model known, current not in repo).  These are
  MODELED consumption assumptions, not measured ratings; the sim must never
  be read as a rating of the unselected motors.

Output: c2.1/results/power_sim.json with the instantaneous draw timeline and
peak vs the 500 W operating budget.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]

PSU = json.loads((REPO / "design/parameters.json").read_text())["psu"]
OPERATIONAL_CAP_W = float(PSU["operational_cap_W"])
PSU_CURRENT_DERIVED_W = float(PSU["current_derived_ceiling_W"])
PSU_NAMEPLATE_W = float(PSU["nameplate_W"])

# Stage schedule of the virtual duty cycle (seconds).
HEAT_UP_END_S = 300
SHREDDING_END_S = 600
STEADY_END_S = 1800
BAND_ROTATION_S = 30  # matches firmware BAND_ROTATION_PERIOD_MS


def demand_at(t_s, loads):
    """(demands, stage) at time t_s. loads = {key: W}."""
    stage = ("heat_up" if t_s < HEAT_UP_END_S
             else "shredding" if t_s < SHREDDING_END_S
             else "steady_filament_production")
    fans = True
    h60 = True  # die-region cartridge thermostat holds setpoint in all stages
    m1 = HEAT_UP_END_S <= t_s < STEADY_END_S + 1200  # shredding + production
    m2 = t_s >= SHREDDING_END_S
    return ({"fans": fans, "h60": h60, "m1": m1, "m2": m2}, stage)


def admitted_load(t_s, loads, demands, aux_demand_W=0.0,
                  budget_W=OPERATIONAL_CAP_W):
    """Apply the controller's priority allocator and hard modeled budget."""
    budget_W = min(budget_W, OPERATIONAL_CAP_W)
    load = 0.0
    admitted = {"rejected_demands": 0}
    for key in ("fans", "h60", "m1", "m2"):
        if demands[key]:
            if load + loads[key] <= budget_W:
                admitted[key] = True
                load += loads[key]
            else:
                admitted["rejected_demands"] += 1
    if aux_demand_W > 0:
        if load + aux_demand_W <= budget_W:
            admitted["aux"] = True
            load += aux_demand_W
        else:
            admitted["rejected_demands"] += 1
    # At most one EX-H100 band; rotate priorities, trying the next candidate
    # only if the current candidate cannot fit the operating budget.
    first = (t_s // BAND_ROTATION_S) % 3
    for offset in range(3):
        band = (first + offset) % 3
        if load + loads["h100"] <= budget_W:
            admitted["h100_band"] = band
            load += loads["h100"]
            break
        admitted["rejected_demands"] += 1
    return load, admitted


def main():
    electrical = json.loads((C21 / "results/electrical_load.json").read_text())
    devices = {d["device"]: d for d in electrical["electrical_load"]["devices"]}
    h100_w = next(d["W"] for d in electrical["electrical_load"]["devices"]
                  if "EX-H100" in d["device"])
    loads = {
        "fans": devices["COOL-FAN (Sanyo 9RA0824H1001)"]["subtotal_W"],
        "h60": devices["EX-H60 cartridge heater"]["W"],
        "m1": devices["M1 shredder drive (TRK-60127-2460 + GMP60)"]["W"],
        "m2": devices["M2 extruder drive (TRK-6097-2425 + GMP60)"]["W"],
        "h100": h100_w,
    }
    grades = {
        "fans": devices["COOL-FAN (Sanyo 9RA0824H1001)"]["grade"],
        "h60": devices["EX-H60 cartridge heater"]["grade"],
        "m1": devices["M1 shredder drive (TRK-60127-2460 + GMP60)"]["grade"],
        "m2": devices["M2 extruder drive (TRK-6097-2425 + GMP60)"]["grade"],
        "h100": h100_w and devices[
            next(k for k in devices if "EX-H100" in k)]["grade"],
    }

    timeline = []
    per_stage = {}
    for t_s in range(0, STEADY_END_S):
        demands, stage = demand_at(t_s, loads)
        load, admitted = admitted_load(t_s, loads, demands)
        timeline.append({"t_s": t_s, "stage": stage, "draw_W": round(load, 3),
                         "h100_band": admitted.get("h100_band")})
        rec = per_stage.setdefault(stage, {"samples": 0, "peak_W": 0.0,
                                           "sum_W": 0.0})
        rec["samples"] += 1
        rec["sum_W"] += load
        rec["peak_W"] = max(rec["peak_W"], load)
    windows = {"heat_up": [0, HEAT_UP_END_S],
               "shredding": [HEAT_UP_END_S, SHREDDING_END_S],
               "steady_filament_production": [SHREDDING_END_S, STEADY_END_S]}
    stages = {name: {"samples": rec["samples"],
                     "peak_W": round(rec["peak_W"], 3),
                     "mean_W": round(rec["sum_W"] / rec["samples"], 3),
                     "window_s": windows[name]}
              for name, rec in per_stage.items()}

    peak = max(rec["peak_W"] for rec in per_stage.values())
    result = {
        "revision": "C2.1-P6+VP1-STAGE5",
        "module": "c2.1/src/power_sim.py",
        "controller": "c2.1/firmware/controller_core.cpp staged concurrency "
                      "allocator (500 W hard modeled operating budget; 792 W "
                      "PSU current-derived hardware maximum; single-band "
                      "EX-H100 mutual exclusion)",
        "duty_cycle": {
            "heat_up_s": [0, HEAT_UP_END_S],
            "shredding_s": [HEAT_UP_END_S, SHREDDING_END_S],
            "steady_filament_production_s": [SHREDDING_END_S, STEADY_END_S],
            "resolution_s": 1,
            "band_rotation_period_s": BAND_ROTATION_S,
        },
        "modeled_devices": [
            {"key": key, "device": next(k for k in devices if
             (k.startswith("EX-H100") if key == "h100" else
              k.startswith("COOL-FAN") if key == "fans" else
              k.startswith("EX-H60") if key == "h60" else
              k.startswith("M1") if key == "m1" else k.startswith("M2"))),
             "W": loads[key], "grade": grades[key],
             "meaning": ("MODELED consumption from nameplate current x 24 V; "
                         "motor not owned, NOT a rating" if grades[key] == "UNRATED_ESTIMATE"
                         else "nameplate value from design/assembly.json part name")}
            for key in ("m1", "m2", "fans", "h60", "h100")
        ],
        "unrated_assumptions": {
            "statement": "M1 (196.8 W) and M2 (43.2 W) and the fan pair "
                         "(16 W) are UNRATED_ESTIMATE values: the motors are "
                         "not-owned references and the fan current is not in "
                         "the repo. They bound the modeled draw but are not "
                         "measured ratings.",
            "modeled_consumption_only": True,
        },
        "per_stage": stages,
        "peak_W": round(peak, 3),
        "power_policy": "500 W HARD modeled operating budget: refuse each "
                        "next demand above it. PSU 24 V / 33 A = 792 W "
                        "current-derived hardware maximum (800 W nameplate), "
                        "not operating permission. Hardware current limiting "
                        "and EL interlocks stand.",
        "operational_cap_W": OPERATIONAL_CAP_W,
        "psu_current_derived_ceiling_W": PSU_CURRENT_DERIVED_W,
        "psu_nameplate_W": PSU_NAMEPLATE_W,
        "peak_vs_budget_headroom_W": round(OPERATIONAL_CAP_W - peak, 3),
        "peak_within_operational_budget": peak <= OPERATIONAL_CAP_W,
        "modeled_scenarios": [
            {"scenario": "566 W requested (316 W base + 150 W aux + 100 W band)",
             "requested_W": 566.0,
             "admitted_W": admitted_load(600, loads, {"fans": True, "h60": True,
                                  "m1": True, "m2": True}, 150.0)[0],
             "outcome": "aux admitted first; band refused at 500 W"},
            {"scenario": "816 W requested (316 W base + 500 W aux + 100 W band)",
             "requested_W": 816.0,
             "admitted_W": admitted_load(600, loads, {"fans": True, "h60": True,
                                  "m1": True, "m2": True}, 500.0)[0],
             "outcome": "aux refused; one band admitted below 500 W"}],
        "instantaneous_draw_timeline": timeline,
        "timeline_note": "per-second admitted nameplate draw under the "
                         "controller allocator; heater duty cycling limits the "
                         "simulated demand to one EX-H100 band + EX-H60",
        "limitations": [
            "virtual duty cycle over NAMEPLATE/UNRATED device values; no "
            "measured load, thermal lag or duty modulation of thermostat "
            "bands is modeled",
            "UNRATED motor values are consumption estimates for margin "
            "sizing, not nameplates of owned devices",
            "no target firmware build, flash, or energization (all HOLD)",
        ],
        "passed": None,
    }
    ok = (result["peak_within_operational_budget"]
          and all(rec["peak_W"] <= OPERATIONAL_CAP_W
                  for rec in per_stage.values()))
    result["passed"] = ok
    (C21 / "results/power_sim.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "instantaneous_draw_timeline"}, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()