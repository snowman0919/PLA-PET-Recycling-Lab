#!/usr/bin/env python3
"""조립 갱신의 파일/manifest 보존 및 반복 실행 검증. CAD 정확성은 별도 검사."""
import csv
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cad/freecad/final_v08"))
import generate

with tempfile.TemporaryDirectory() as directory:
    out = Path(directory)
    untouched = out / "cnc_parts/keep.step"
    untouched.parent.mkdir()
    untouched.write_bytes(b"preserved non-assembly fixture")
    manifest = out / "step_manifest.csv"
    manifest.write_text("file,status,release_gate\ncnc_parts/keep.step,HOLD,USER_APPROVAL_REQUIRED\nassembly/PPR-FULL-ASM.step,PASS,OLD\n")
    def fake_export(path, objects):
        path.write_bytes(b"assembly fixture")
        return {"file": str(path.relative_to(out)), "status": "PASS", "solid_count": 1}
    with patch.object(generate, "OUT", out), patch.object(sys, "argv", ["generate.py", "--refresh-assemblies"]), patch.object(generate, "final_objects", return_value=[]), patch.object(generate, "export_assembly_metadata"), patch.object(generate, "export", side_effect=fake_export), patch.object(generate.shutil, "rmtree", side_effect=AssertionError("unexpected directory deletion")):
        generate.main()
        first = manifest.read_bytes()
        generate.main()
    assert manifest.read_bytes() == first
    assert untouched.read_bytes() == b"preserved non-assembly fixture"
    with manifest.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 7 and len({r["file"] for r in rows}) == 7
    kept = next(r for r in rows if r["file"] == "cnc_parts/keep.step")
    assert kept["status"] == "HOLD" and kept["release_gate"] == "USER_APPROVAL_REQUIRED"
    assert next(r for r in rows if r["file"] == "assembly/PPR-FULL-ASM.step")["release_gate"] == "OLD"
    assert all(r["release_gate"] for r in rows)
print("ASSEMBLY_REFRESH_PRESERVATION_PASS")
