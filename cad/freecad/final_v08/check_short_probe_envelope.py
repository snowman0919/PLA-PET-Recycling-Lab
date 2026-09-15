#!/usr/bin/env python3
"""Ø3×15 후보의 노출 카트리지 공간만 검사. 삽입/리드/고정 승인 아님."""
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import Part
from generate import final_objects
from check_retainer_tool_access import overlaps

ROOT = Path(__file__).resolve().parents[3]


def main():
    shapes = {item["name"]: item["shape"] for item in final_objects()}
    rows = []
    for zone, sensor_z in enumerate((95, 170, 245), 1):
        name = f"TemperatureProbeT{zone}"
        assert name in shapes
        exposed = Part.makeCylinder(1.5, 15-5.2, App.Vector(375-sensor_z, 364, 382), App.Vector(0, 1, 0))
        assert exposed.isValid() and len(exposed.Solids) == 1
        assert overlaps(exposed, {"negative_control": exposed.copy()})
        collisions = overlaps(exposed, {n: s for n, s in shapes.items() if n != name})
        rows.append({"channel": name, "nominal_external_length_mm": 9.8,
                     "collisions": collisions, "external_envelope_check": "FAIL" if collisions else "PASS"})
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN", "rows": rows,
              "scope": "Nominal OD3 length15 cartridge, assumed insertion5.2; only exposed9.8 checked. Existing probe object including its lead excluded for each replacement. No diameter tolerance, insertion geometry, tip/junction, connector, lead, retention or temperature accuracy qualification.",
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                  Path(__file__).resolve(), Path(__file__).with_name("generate.py"),
                  Path(__file__).with_name("check_retainer_tool_access.py"),
                  ROOT/"cad/freecad/compact/geometry.py", ROOT/"cad/parameters/final_v08.json",
                  ROOT/"docs/final/probe_sourcing_ko.md")}}
    (ROOT/"analysis/final_validation/results/v0.8/short_probe_envelope.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
