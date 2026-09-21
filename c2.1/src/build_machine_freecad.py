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


def main():
    config = json.loads((C21/"design/machine_integration.json").read_text())
    master = json.loads((REPO/config["legacy_master"]).read_text())
    overrides = config["legacy_instance_y_overrides_mm"]
    doc = App.newDocument("PPR_C2_1_machine")
    for item in master["instances"]:
        if item["group"] == config["excluded_legacy_group"]:
            continue
        obj = doc.addObject("Part::Feature", "Legacy_%03d" % len(doc.Objects))
        obj.Label = item["name"]
        obj.Shape = read_shape(REPO/"cad/parts"/(item["part"]+".step"))
        at = list(item["at"])
        if item["name"] in overrides:
            at[1] = overrides[item["name"]]
        r = item["rotation"]
        obj.Placement = App.Placement(App.Vector(*at), App.Rotation(App.Vector(*r[:3]), r[3]))
        obj.addProperty("App::PropertyString", "PartID")
        obj.PartID = item["part"]
        obj.addProperty("App::PropertyString", "Qualification")
        obj.Qualification = "C1_INTERFACE_REFERENCE"

    c2 = doc.addObject("Part::Feature", "C2_1_S2_Subassembly")
    c2.Label = "C2.1 S2 checked subassembly"
    c2.Shape = read_shape(C21/"cad/PPR_C2_1_S2_transmission.step")
    t = config["c2_subassembly_transform"]
    c2.Placement = App.Placement(App.Vector(*t["translation_mm"]),
                                 App.Rotation(App.Vector(*t["rotation_axis"]), t["rotation_deg"]))
    c2.addProperty("App::PropertyString", "Qualification")
    c2.Qualification = "DIGITAL_KINEMATIC_PASS_RATING_HOLD"
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
