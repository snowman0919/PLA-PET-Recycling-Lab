#!/usr/bin/env python3
"""중간 JSON이 그대로여도 CAD 원본 변경을 거부한다."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/final_validation"))
from retainer_support_sensitivity import verify_sources
import retainer_support_sensitivity as support

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "geometry.py"
    source.write_text("original")
    evidence = root / "candidate.json"
    evidence.write_text(json.dumps({"source_sha256": {
        source.name: hashlib.sha256(source.read_bytes()).hexdigest()}}))
    report = {"source_sha256": {
        evidence.name: hashlib.sha256(evidence.read_bytes()).hexdigest()}}
    verify_sources(report, root)
    source.write_text("changed")
    try:
        verify_sources(report, root)
    except AssertionError as error:
        assert str(error) == source.name
    else:
        raise AssertionError("Changed CAD source accepted through unchanged evidence")
    (root / "retainer_candidate_fea.json").write_text(json.dumps(report))
    for mesh, filename in ((".5", "retainer_support_sensitivity.json"),
                           (".7", "retainer_support_sensitivity_0.7.json")):
        output = root / filename
        output.write_text(json.dumps({"status": "HOLD", "element_benchmark": "PASS"}))
        with patch.object(support.qualification, "OUT", root / "unused.json"), \
             patch.object(support.qualification, "ROOT", root), \
             patch.object(sys, "argv", ["support", "--mesh", mesh]):
            try:
                support.main()
            except AssertionError as error:
                assert str(error) == source.name
            else:
                raise AssertionError("Stale candidate accepted")
        assert json.loads(output.read_text()) == {
            "status": "INCOMPLETE", "physical_validation_state": "NOT_RUN"}
print("RETAINER_SOURCE_CHAIN_PASS")
