#!/usr/bin/env python3
"""현행 축의 최장 인접 커터–기어 구간: 접촉/강도 승인 아닌 해석 입력."""
import json
import sys
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
sys.path.insert(0, str(ROOT / "analysis/final_validation"))
from geometry import cutter_shaft
from run_phase_section_sensitivity_v08 import torsion_cases
from run_calculix_v08 import sha256, INPUT


def main():
    manifest = INPUT / "geometry_manifest.json"
    geometry = json.loads(manifest.read_text())
    source = ROOT / "cad/freecad/compact/geometry.py"
    assert geometry["geometry_source_sha256"] == sha256(source)
    parameters = ROOT / "cad/parameters/baseline.json"
    settings = json.loads(parameters.read_text())["shredder"]
    cases = torsion_cases(geometry["shredder_stations"], settings["mechanical_relief_torque_nm"], settings["shaft_diameter_mm"])
    case = max(cases, key=lambda row: sum(row["series_lengths_mm"]))
    rows = []
    folder = ROOT / "analysis/final_validation/results/v0.8"
    for key, cut in (("153", case["adjacent_driven_cutter_y_mm"]), ("105", case["jammed_slave_cutter_y_mm"])):
        station = geometry["shredder_stations"][key]
        start = cut - station["shaft_y_min_mm"]
        length = station["gear_y_mm"] - cut
        assert 0 <= start < start + length <= 240
        shape = cutter_shaft().common(Part.makeBox(22, length, 22, App.Vector(-11, start, -11)))
        shape.translate(App.Vector(0, -start, 0))
        assert shape.isValid() and len(shape.Solids) == 1
        assert abs(shape.BoundBox.YMin) < 1e-7 and abs(shape.BoundBox.YMax - length) < 1e-7
        path = folder / f"torsion_load_path_{key}.step"
        shape.exportStep(str(path))
        restored = Part.read(str(path))
        error = abs(restored.Volume - shape.Volume) / shape.Volume
        assert restored.isValid() and len(restored.Solids) == 1 and error < 1e-6
        rows.append({"shaft": key, "global_cut_y_mm": cut, "global_gear_y_mm": station["gear_y_mm"],
                     "local_original_start_mm": start, "length_mm": length,
                     "step": str(path.relative_to(ROOT)), "step_sha256": sha256(path), "relative_volume_error": error})
    assert sum(row["length_mm"] for row in rows) == sum(case["series_lengths_mm"])
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN", "spans": rows,
              "load_case": case,
              "scope": "Current baseline keyways, not extended slave candidate. Maximum ideal-round adjacent-pair span only; not proof of worst keyed compliance. Input through driven rear gear to one jammed slave cutter, driven cutting resistance zero. Cut-face loading/constraint still to solve; hub/key/gear contact excluded.",
              "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (Path(__file__).resolve(), source, manifest, parameters, ROOT / "analysis/final_validation/run_phase_section_sensitivity_v08.py")}}
    (folder / "torsion_load_path_geometry.json").write_text(json.dumps(result, indent=2) + "\n")
    print("TORSION_LOAD_PATH_GEOMETRY_HOLD", [(r["shaft"], r["length_mm"]) for r in rows])


if __name__ == "__main__":
    main()
