"""Create the native FreeCAD C2.1 machine assembly from checked STEP parts."""
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]


def read_shape(path):
    shape = Part.Shape()
    shape.read(str(path))
    if shape.isNull() or not shape.isValid():
        raise RuntimeError("Invalid STEP shape: "+str(path))
    return shape


# VP1 Stage 1: instances rebuilt with real tooth geometry (part ids kept).
# Shapes come from c2.1/cad/parts_stage1 (exported by drive_teeth.py).
STAGE1_REPLACEMENT_PART = {
    "DRV-SH15R_001": "DRV-SH15R", "DRV-SH15L_001": "DRV-SH15L",
    "DRV_SH40L_lower": "DRV-SH40L", "DRV_SH40R_upper": "DRV-SH40R",
    "DRV-SP24-B20_001": "DRV-SP24-B20", "DRV-SP24-B25_001": "DRV-SP24-B25",
    "DRV-SP24-B12_001": "DRV-SP24-B12", "DRV-SP12-B12_001": "DRV-SP12-B12",
}
STAGE1_NEW_PARTS = (["DRV-CHAIN-A", "DRV-CHAIN-B", "CHUTE_BODY",
                     "CHUTE_TROUGH_FLOOR_E", "GUARD_S2_RING",
                     "GUARD_CHAIN_A", "GUARD_CHAIN_B",
                     "GUARD_LID_INTERLOCK_SEAT", "PULL_FRAME",
                     "PULL_ROLLER_FIXED", "PULL_ROLLER_ADJ", "PULL_NIP_STOP",
                     "PULL_MOTOR_REF", "WIND_SPOOL_SHAFT", "WIND_SPOOL_DRUM",
                     "WIND_FLANGE_L", "WIND_FLANGE_R", "WIND_MOTOR_REF",
                     "WIND_TRAVERSE_SCREW", "WIND_TRAVERSE_RIDER",
                     "WIND_TENSIONER", "EL_DIN_RAIL", "EL_DRIVER_1",
                     "EL_DRIVER_2", "EL_DRIVER_3", "EL_CONTACTOR",
                     "EL_ESTOP_BOX", "EL_OVERTEMP_BOX", "EL_WIRE_DUCT"])


def main():
    config = json.loads((C21/"design/machine_integration.json").read_text())
    stage3 = json.loads((C21/"results/machine_integration.json").read_text())
    relieved_instances = set(stage3.get("vp1_stage3", {}).get("relieved_instances", []))
    master = json.loads((REPO/config["legacy_master"]).read_text())
    overrides = config["legacy_instance_y_overrides_mm"]
    doc = App.newDocument("PPR_C2_1_machine")
    for item in master["instances"]:
        if item["group"] == config["excluded_legacy_group"]:
            continue
        obj = doc.addObject("Part::Feature", "Legacy_%03d" % len(doc.Objects))
        obj.Label = item["name"]
        repl = STAGE1_REPLACEMENT_PART.get(item["name"])
        relief = item["name"] in relieved_instances
        if repl:
            obj.Shape = read_shape(C21/"cad/parts_stage1"/(repl+".step"))
        elif relief:
            obj.Shape = read_shape(C21/"cad/parts_stage1"/(item["name"]+".step"))
        else:
            obj.Shape = read_shape(REPO/"cad/parts"/(item["part"]+".step"))
        at = list(item["at"])
        if item["name"] in overrides:
            at[1] = overrides[item["name"]]
        r = item["rotation"]
        obj.Placement = App.Placement(App.Vector(*at), App.Rotation(App.Vector(*r[:3]), r[3]))
        obj.addProperty("App::PropertyString", "PartID")
        obj.PartID = item["part"]
        obj.addProperty("App::PropertyString", "Qualification")
        obj.Qualification = ("VP1_STAGE1_REAL_TEETH" if repl else
                             "VP1_STAGE3_RELIEVED" if relief else
                             "C1_INTERFACE_REFERENCE")

    c2 = doc.addObject("Part::Feature", "C2_1_S2_Subassembly")
    c2.Label = "C2.1 S2 checked subassembly"
    c2.Shape = read_shape(C21/"cad/PPR_C2_1_S2_transmission.step")
    t = config["c2_subassembly_transform"]
    c2.Placement = App.Placement(App.Vector(*t["translation_mm"]),
                                 App.Rotation(App.Vector(*t["rotation_axis"]), t["rotation_deg"]))
    c2.addProperty("App::PropertyString", "Qualification")
    c2.Qualification = "DIGITAL_KINEMATIC_PASS_RATING_HOLD"
    for name in STAGE1_NEW_PARTS:
        obj = doc.addObject("Part::Feature", "VP1_%03d" % len(doc.Objects))
        obj.Label = name
        obj.Shape = read_shape(C21/"cad/parts_stage1"/(name+".step"))
        obj.addProperty("App::PropertyString", "PartID")
        obj.PartID = name
        obj.addProperty("App::PropertyString", "Qualification")
        obj.Qualification = "VP1_STAGE1_NEW_PART"
    doc.recompute()
    out = C21/"cad/PPR_C2_1_machine_integration.FCStd"
    doc.saveAs(str(out))
    result = {
        "freecad_version": App.Version(),
        "objects": len(doc.Objects),
        "valid_objects": sum(obj.Shape.isValid() for obj in doc.Objects),
        "file": str(out.relative_to(REPO)),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "bytes": out.stat().st_size,
        "source": str(HERE.relative_to(REPO)),
        "source_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "physical_release": "HOLD"
    }
    (C21/"results/machine_freecad.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    if result["objects"] != result["valid_objects"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
