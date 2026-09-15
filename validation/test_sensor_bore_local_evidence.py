"""센서 보어 3D 열-압력 screen의 출처·수렴·평형 증거를 검사한다."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json").read_text())
assert report["status"] == "PASS" and report["physical_validation_state"] == "NOT_RUN"
assert all(report["checks"].values()) and "strength remains conditional" in report["qualification_scope"]
assert len(report["meshes"]) == 4 and report["medium_to_fine_regional_stress_change"] <= .05
assert report["geometry"]["minimum_flat_tip_ligament_mm"] >= 3.32
assert report["conditional_temperature_boundary_c"] == {"inner": 270.0, "outer": 245.0}
assert all(math.isfinite(row["sensor_region_peak_stress_mpa"]) and row["sensor_region_peak_stress_mpa"] > 0 for row in report["meshes"])
assert all(row["temperature_range_c"] == [245.0, 270.0] and len(row["thermal_deck_sha256"]) == 64
           for row in report["meshes"])
assert all(math.sqrt(sum(v*v for v in row["applied_net_force_n"])) < .01 for row in report["meshes"])
assert all((ROOT / path).is_file() and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
           for path, digest in report["source_sha256"].items())
print(f"SENSOR_BORE_LOCAL_EVIDENCE_PASS stress_mpa={report['meshes'][-1]['sensor_region_peak_stress_mpa']:.3f} status=PASS material=CONDITIONAL")
