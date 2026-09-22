"""VP1 Stage 2: electrical bay CAD (above the owned PSU) + aggregate load.

The owned PSU (240x120x65 box) sits at (370..610, 40..160, 30..95); the bay
occupies the free volume directly above it (z 95..165).  Parts:
- EL_DIN_RAIL: 35 mm top-hat rail (simplified prism) x 385..595.
- EL_DRIVER_1/2/3: stepper/BLDC driver bodies clipped on the rail
  (M1, M2, spool/puller accessory drives).
- EL_CONTACTOR: safety contactor body (branch fuse + contactor function
  from the machine_wiring net list).
- EL_ESTOP_BOX: dual-channel E-stop / lid / service interlock relay box.
- EL_WIRE_DUCT: slotted wiring duct over the rail row.
Each part is a single solid, collision-free against the retained assembly
(audited in build_machine_integration.py).

Aggregate load (results/electrical_load.json): nameplate values taken only
from existing repo sources (design/parameters.json, design/assembly.json
part names).  M1/M2 are NOT OWNED references (parameters.json status
MANUFACTURER_REFERENCE_NOT_OWNED) -> their loads are UNRATED estimates
(nameplate current x 24 V), evidence grade UNRATED_ESTIMATE.
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq

V = cq.Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

PSU = dict(x0=370.0, x1=610.0, y0=40.0, y1=160.0, z1=95.0)
BAY_Z0 = 95.0
RAIL_Z = (100.0, 103.0, 135.0)  # rail bottom, top, driver top


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def din_rail():
    """35 mm top-hat rail (simplified: spine + flanges), x 385..595."""
    spine = _box(385.0, 595.0, 46.0, 49.0, RAIL_Z[0], RAIL_Z[1])
    f1 = _box(385.0, 595.0, 42.0, 46.0, RAIL_Z[1] - 2.0, RAIL_Z[1])
    f2 = _box(385.0, 595.0, 49.0, 53.0, RAIL_Z[1] - 2.0, RAIL_Z[1])
    return spine.fuse(f1).fuse(f2).clean()


def driver(idx, x0):
    """Driver body on the rail: 45x40x35."""
    return _box(x0, x0 + 45.0, 42.0, 82.0, RAIL_Z[1], RAIL_Z[2])


def driver_1():
    return driver(1, 390.0)


def driver_2():
    return driver(2, 445.0)


def driver_3():
    return driver(3, 500.0)


def contactor():
    """Safety contactor body: 45x45x70 at the rail's east end."""
    return _box(550.0, 595.0, 42.0, 87.0, RAIL_Z[1], RAIL_Z[1] + 70.0)


def estop_box():
    """Dual-channel E-stop / lid / service interlock relay box (north row)."""
    return _box(390.0, 430.0, 100.0, 140.0, BAY_Z0, BAY_Z0 + 40.0)


def overtemp_box():
    """Manual-reset independent overtemperature relay box (safety_retained)."""
    return _box(440.0, 480.0, 100.0, 140.0, BAY_Z0, BAY_Z0 + 40.0)


def wire_duct():
    """Slotted wiring duct along the north edge of the bay."""
    return _box(385.0, 595.0, 140.0, 145.0, BAY_Z0, BAY_Z0 + 30.0)


def current_limiter():
    """Heater sequencer / current-limit relay bank (staged heater power
    control hardware position, ADR in electrical_load.json)."""
    return _box(490.0, 530.0, 100.0, 140.0, BAY_Z0, BAY_Z0 + 40.0)


def components():
    """Named electrical bay parts (group 'electrical')."""
    return [("EL_DIN_RAIL", din_rail()),
            ("EL_DRIVER_1", driver_1()),
            ("EL_DRIVER_2", driver_2()),
            ("EL_DRIVER_3", driver_3()),
            ("EL_CONTACTOR", contactor()),
            ("EL_ESTOP_BOX", estop_box()),
            ("EL_OVERTEMP_BOX", overtemp_box()),
            ("EL_CURRENT_LIMITER", current_limiter()),
            ("EL_WIRE_DUCT", wire_duct())]


def load_inventory():
    """Per-device W from nameplate values in EXISTING repo sources only.

    Evidence grades:
    - NAMEPLATE_SOURCE: value printed in design/assembly.json part name or
      design/parameters.json (heaters, PSU).
    - UNRATED_ESTIMATE: motor not owned (parameters.json status
      MANUFACTURER_REFERENCE_NOT_OWNED); nameplate current x 24 V as an
      estimate, not a rating.
    """
    params = json.loads((REPO / "design/parameters.json").read_text())
    devices = [
        {"device": "M1 shredder drive (TRK-60127-2460 + GMP60)",
         "nameplate": "8.2 A @ 24 V (parameters.json M1.rated_A)",
         "W": 8.2 * 24.0, "count": 1, "owned": False,
         "grade": "UNRATED_ESTIMATE"},
        {"device": "M2 extruder drive (TRK-6097-2425 + GMP60)",
         "nameplate": "1.8 A @ 24 V (parameters.json M2.rated_A)",
         "W": 1.8 * 24.0, "count": 1, "owned": False,
         "grade": "UNRATED_ESTIMATE"},
        {"device": "EX-H100 band heater",
         "nameplate": "24 V 100 W (design/assembly.json part name)",
         "W": 100.0, "count": 3, "owned": True,
         "grade": "NAMEPLATE_SOURCE"},
        {"device": "EX-H60 cartridge heater",
         "nameplate": "24 V 60 W (design/assembly.json part name)",
         "W": 60.0, "count": 1, "owned": True,
         "grade": "NAMEPLATE_SOURCE"},
        {"device": "COOL-FAN (Sanyo 9RA0824H1001)",
         "nameplate": "model only; current not in repo",
         "W": 8.0, "count": 2, "owned": True,
         "grade": "UNRATED_ESTIMATE"},
    ]
    for d in devices:
        d["subtotal_W"] = d["W"] * d["count"]
    total = sum(d["subtotal_W"] for d in devices)
    # Staged heater power control (design decision, VP1 Stage 3): the
    # controller sequences the heater bands so at most ONE EX-H100 band plus
    # the EX-H60 cartridge draw at any instant (160 W of heater load); motors
    # and fans are continuous.  Control logic is UNIMPLEMENTED_IN_FIRMWARE;
    # a hardware interlock (EL_CURRENT_LIMITER relay bank) is required so a
    # firmware fault cannot energize two bands.
    staged_heaters = 100.0 + 60.0
    continuous = total - 100.0 * 3 - 60.0  # motors + fans
    staged_peak = continuous + staged_heaters
    cap = params["psu"]["operational_cap_W"]
    return {
        "psu": {"V": params["psu"]["V"], "rated_W": params["psu"]["rated_W"],
                "operational_cap_W": cap,
                "body_mm": params["psu"]["body_mm"], "owned": True},
        "devices": devices,
        "total_peak_W": total,
        "staged_peak_W": staged_peak,
        "staged_schedule": {
            "policy": "at most 1x EX-H100 band + EX-H60 cartridge at any "
                      "instant; bands rotate on controller timing",
            "heater_W_staged": staged_heaters,
            "continuous_W": continuous,
            "control_implementation": "UNIMPLEMENTED_IN_FIRMWARE",
            "hardware_interlock": "EL_CURRENT_LIMITER relay bank required "
                                  "so a firmware fault cannot energize two "
                                  "bands (documented requirement)",
        },
        "operational_cap_W": cap,
        "headroom_W": cap - total,
        "staged_headroom_W": cap - staged_peak,
        "cap_exceeded": total > cap,
        "staged_cap_exceeded": staged_peak > cap,
        "note": ("PEAK simultaneous nameplate sum. M1/M2 are not-owned "
                 "references -> UNRATED estimates, not ratings. Heater duty "
                 "cycling lowers the MEAN load but not the peak; the peak "
                 "exceeds the 500 W operating cap - documented defect, "
                 "mitigation: two-band operation or PSU/cap revision."),
    }


def main():
    parts = components()
    recs = []
    for name, solid in parts:
        if not solid.isValid() or len(solid.Solids()) != 1:
            raise RuntimeError("invalid electrical part " + name)
        b = solid.BoundingBox()
        recs.append({"name": name, "solids": len(solid.Solids()),
                     "bounds": [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]})
        path = ROOT / "cad/parts_stage1" / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
    load = load_inventory()
    result = {"parts": recs, "electrical_load": load,
              "passed": True}
    (ROOT / "results" / "electrical_load.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
