#!/usr/bin/env python3
"""같은 Git commit에서도 작업트리 파일이 바뀌면 과거 ZIP을 거부해야 한다."""

import sys
import io
import zipfile
import json
from copy import deepcopy
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release"))
from verify_fabrication_release import digest, verify_current_source, verify_layout
from build_fabrication_release import validate_gate_reports, zi
import build_fabrication_release as builder
from firmware_evidence import firmware_evidence_current
from build_electrical_firmware_release import rebuild_script


def main():
    payloads = []
    for _ in range(2):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as package:
            package.writestr(zi("section/example.txt"), b"repeatable payload")
        payloads.append(stream.getvalue())
    assert payloads[0] == payloads[1]
    with zipfile.ZipFile(io.BytesIO(payloads[0])) as package:
        info = package.getinfo("section/example.txt")
        assert info.compress_type == zipfile.ZIP_STORED and info.create_system == 3
    print("FABRICATION_STORED_ZIP_REPEATABILITY_PASS")
    required = {"section/a": (Path("a"), "a"), "section/b": (Path("b"), "b")}
    listed = {"section/a": {"source": "a"}, "section/b": {"source": "b"}}
    verify_layout(listed, required)
    for invalid in ({"section/a": listed["section/a"]},
                    {**listed, "section/c": {"source": "c"}},
                    {**listed, "section/a": {"source": "b"}}):
        try:
            verify_layout(invalid, required)
        except AssertionError:
            pass
        else:
            raise AssertionError("Incomplete or remapped package accepted")
    print("FABRICATION_LAYOUT_NEGATIVE_TESTS_PASS cases=3")
    script = ROOT / "exports/final/firmware/reproducible_build/build_and_verify.py"
    assert script.read_text() == rebuild_script(), "released rebuild script differs from generator"
    assert firmware_evidence_current(ROOT), "current firmware evidence mismatch"
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for rel in ("firmware/arduino_mega", "exports/final/firmware", "exports/final/drive_ggm_v08/firmware", "control/ggm_drive_contract.json"):
            if (ROOT / rel).is_file():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, root / rel)
                continue
            shutil.copytree(ROOT / rel, root / rel)
        assert firmware_evidence_current(root)
        for rel in ("exports/final/drive_ggm_v08/firmware/arduino_mega/src/board_config.h",
                    "exports/final/firmware/source/arduino_mega/src/board_config.h"):
            path = root / rel
            original = path.read_bytes()
            path.write_bytes(original + b"\n// changed\n")
            assert not firmware_evidence_current(root), rel
            path.write_bytes(original)
        added = root / "exports/final/drive_ggm_v08/firmware/arduino_mega/src/unlisted.cpp"
        added.write_text("// unlisted compile input\n")
        assert not firmware_evidence_current(root), "unlisted source accepted"
        fw = root / "exports/final/firmware"
        lock_path = fw / "library_lock.json"
        original_lock = json.loads(lock_path.read_text())
        for kind in ("board", "core", "library"):
            lock = deepcopy(original_lock)
            if kind == "board": lock["fqbn"] = "arduino:avr:uno"
            elif kind == "core": lock["platforms"][0]["version"] = "0.0.0"
            else: lock["libraries"] = [{"name": "unexpected", "version": "1.0"}]
            lock_path.write_text(json.dumps(lock))
            result = subprocess.run([sys.executable, str(fw / "reproducible_build/build_and_verify.py")], capture_output=True, text=True)
            assert result.returncode != 0 and ("mismatch" in result.stderr or "external libraries" in result.stderr), result.stderr
    print("FIRMWARE_TOOLCHAIN_LOCK_NEGATIVE_TESTS_PASS cases=3")
    print("FIRMWARE_SOURCE_BINDING_NEGATIVE_TESTS_PASS cases=3")
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "drawing.txt"
        source.write_text("old dimension")
        item = {"source": source.name, "size": source.stat().st_size, "sha256": digest(source)}
        verify_current_source(root, item)
        # Same size change defeats a size-only or unchanged-commit check.
        source.write_text("new dimension")
        try:
            verify_current_source(root, item)
        except AssertionError as error:
            assert "source changed" in str(error)
        else:
            raise AssertionError("stale package source accepted")
    print("FABRICATION_SOURCE_FRESHNESS_REGRESSION_PASS")
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder); source = root / "payload.txt"; source.write_text("clean")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", source.name], cwd=root, check=True)
        subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], cwd=root, check=True)
        files = {"section/payload.txt": (source, source.name)}
        with patch.object(builder, "ROOT", root):
            builder.validate_payload_git_state(files)
            source.write_text("dirty")
            try:
                builder.validate_payload_git_state(files)
            except AssertionError as error:
                assert "modified release payload" in str(error)
            else:
                raise AssertionError("dirty payload accepted")
    print("FABRICATION_PAYLOAD_GIT_STATE_NEGATIVE_TEST_PASS")
    inventory = json.loads((ROOT / "validation/results/v08_release_inventory.json").read_text())
    compliance = json.loads((ROOT / "validation/results/v08_full_compliance.json").read_text())
    inventory["checks"] = dict.fromkeys(inventory["checks"], True)
    compliance["checks"] = {key: {"status": "PASS"} for key in compliance["checks"]}
    validate_gate_reports(inventory, compliance)
    for kind in ("empty", "missing", "false_string", "hold", "revision", "section_missing", "section_uncovered", "scope_hold"):
        inv, comp = deepcopy(inventory), deepcopy(compliance)
        if kind == "empty":
            inv["checks"] = {}; comp["checks"] = {}
        elif kind == "missing":
            del comp["checks"]["03_hot_zone_mount"]
        elif kind == "false_string":
            inv["checks"]["solver_evidence"] = "False"
        elif kind == "hold":
            comp["checks"]["06_tolerance_stacks"]["status"] = "HOLD"
        elif kind == "revision":
            comp["revision"] = "old"
        elif kind == "section_missing":
            del comp["section_coverage"]["25"]
        elif kind == "section_uncovered":
            comp["section_coverage"]["03"]["covered"] = False
        else:
            comp["section_coverage"]["01"]["status"] = "FAIL"
        try:
            validate_gate_reports(inv, comp)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"invalid gate report accepted: {kind}")
    print("FABRICATION_GATE_REPORT_NEGATIVE_TESTS_PASS cases=8")


if __name__ == "__main__":
    main()
