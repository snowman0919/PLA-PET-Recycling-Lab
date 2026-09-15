#!/usr/bin/env python3
"""동일 유지판 지지 강성의 두 메시 비교. 체결 강도 판정이 아니다."""
import hashlib
import json
import math
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "analysis/final_validation"))
from retainer_support_sensitivity import verify_sources
folder = root / "analysis/final_validation/results/v0.8"
(folder/"retainer_support_mesh_comparison.json").write_text(json.dumps({"status": "INCOMPLETE", "physical_validation_state": "NOT_RUN"})+"\n")
coarse = json.loads((folder/"retainer_support_sensitivity_0.7.json").read_text())
fine = json.loads((folder/"retainer_support_sensitivity.json").read_text())
assert [coarse["mesh_mm"], fine["mesh_mm"]] == [.7,.5]
for report in (coarse,fine):
    assert report["status"] == "HOLD" and report["element_benchmark"] == "PASS"
    verify_sources(report, root)
    assert len(report["retainer_fixed_mesh_sensitivity"]) == 3
rows = []
for a,b in zip(coarse["retainer_fixed_mesh_sensitivity"],fine["retainer_fixed_mesh_sensitivity"]):
    assert a["per_bore_stiffness_n_mm"] == b["per_bore_stiffness_n_mm"]
    uc,uf = a["result"]["max_displacement_mm"],b["result"]["max_displacement_mm"]
    change = abs(uf-uc)/uf*100
    sc,sf = a["result"]["max_von_mises_mpa"],b["result"]["max_von_mises_mpa"]
    assert all(math.isfinite(value) and value > 0 for value in (uc,uf,sc,sf))
    rows.append({"stiffness_n_mm": b["per_bore_stiffness_n_mm"], "coarse_u_mm": uc,
                 "fine_u_mm": uf, "change_percent": change, "within_5_percent": change <= 5,
                 "coarse_peak_stress_mpa": sc, "fine_peak_stress_mpa": sf,
                 "peak_stress_change_percent": abs(sf-sc)/sf*100})
print(json.dumps(rows, indent=2))
result = {"status": "HOLD", "stress_qualification": "NOT_QUALIFIED", "rows": rows,
          "scope": "Two fixed meshes of a surrogate support distribution; displacement criterion only, no stress or joint-strength acceptance.",
          "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in (Path(__file__).resolve(), folder/"retainer_support_sensitivity_0.7.json", folder/"retainer_support_sensitivity.json")}}
(folder/"retainer_support_mesh_comparison.json").write_text(json.dumps(result, indent=2)+"\n")
assert all(row["within_5_percent"] for row in rows)
print("RETAINER_SUPPORT_TWO_MESH_DISPLACEMENT_PASS assembly=HOLD")
