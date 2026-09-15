"""Read-only transitive SHA-256 audit. Freshness is not engineering acceptance."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

HASH = re.compile(r"[0-9a-f]{64}")
MAP_KEYS = {"source_sha256", "dependencies_sha256", "artifacts_sha256"}
SCALAR_BINDINGS = {
    "analysis/final_validation/results/v0.8/summary.json": {
        "/pipeline_source_sha256": "analysis/final_validation/run_calculix_v08.py",
        "/geometry/geometry_source_sha256": "cad/freecad/compact/geometry.py",
    },
    "analysis/final_validation/results/v0.8/loaded_phase.json": {
        "/source_sha256": "analysis/final_validation/run_phase_load_v08.py",
        "/geometry_source_sha256": "cad/freecad/compact/geometry.py",
    },
    "analysis/final_validation/input/geometry_manifest.json": {
        "/geometry_source_sha256": "cad/freecad/compact/geometry.py",
    },
}

def _pointer(data, pointer):
    for key in pointer.lstrip("/").split("/"):
        data = data[key.replace("~1", "/").replace("~0", "~")]
    return data

def audit_evidence(root: Path, report: str, required_sources=(), scalar_bindings=None):
    """Follow declared source JSON edges; check raw artifacts without interpreting them.

    Includes a second read to detect writes during inspection. Only declared edges
    are covered: callers must maintain required-source contracts for import gaps.
    Does not accept an empty root manifest, a path escape, cycles, or invalid JSON.
    Never rewrites an expected hash and never promotes a stored status to PASS.
    """
    root = Path(root).resolve()
    registry = dict(SCALAR_BINDINGS)
    if scalar_bindings:
        registry.update(scalar_bindings)
    snapshots, reports, active, edges, issues = {}, set(), set(), [], []
    def issue(kind, source, target="", **detail):
        issues.append({"kind": kind, "report": source, "target": target, **detail})
    def path_for(rel):
        if not isinstance(rel, str) or not rel or "\\" in rel:
            raise ValueError("invalid relative path")
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts or str(posix) != rel:
            raise ValueError("non-canonical relative path")
        path = (root / rel).resolve()
        if not path.is_relative_to(root):
            raise ValueError("path escapes root")
        return path
    def read(rel, source):
        try:
            path = path_for(rel)
            content = path.read_bytes()
        except (OSError, ValueError) as exc:
            issue("UNREADABLE_OR_UNSAFE_PATH", source, str(rel), detail=str(exc))
            return None
        digest = hashlib.sha256(content).hexdigest()
        if rel in snapshots and snapshots[rel] != digest:
            issue("CHANGED_DURING_AUDIT", source, rel)
        snapshots[rel] = digest
        return content
    def check_edge(source, target, expected, recurse):
        if not isinstance(expected, str) or not HASH.fullmatch(expected):
            issue("INVALID_DIGEST", source, str(target))
            return
        content = read(target, source)
        if content is None:
            return
        actual = hashlib.sha256(content).hexdigest()
        edges.append({"report": source, "target": target, "expected": expected, "actual": actual})
        if expected != actual:
            issue("HASH_MISMATCH", source, target, expected=expected, actual=actual)
        if recurse and Path(target).suffix.lower() == ".json":
            visit(target)
    def scan(data, source, found, pointer=""):
        if isinstance(data, dict):
            for key, value in data.items():
                where = pointer + "/" + key
                if key in MAP_KEYS and isinstance(value, dict):
                    for target, digest in value.items():
                        found.add(target)
                        check_edge(source, target, digest, key != "artifacts_sha256")
                elif key in MAP_KEYS and isinstance(value, str):
                    if where not in registry.get(source, {}):
                        issue("UNBOUND_SCALAR_DIGEST", source, where)
                elif key in MAP_KEYS:
                    issue("INVALID_MANIFEST_MAP", source, where)
                else:
                    scan(value, source, found, where)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                scan(value, source, found, pointer + "/" + str(i))
    def visit(rel):
        if rel in active:
            issue("DEPENDENCY_CYCLE", rel, rel)
            return
        if rel in reports:
            return
        content = read(rel, rel)
        if content is None:
            return
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("report must be an object")
        except (ValueError, UnicodeDecodeError) as exc:
            issue("INVALID_REPORT_JSON", rel, detail=str(exc))
            return
        active.add(rel)
        found = set()
        scan(data, rel, found)
        for pointer, target in registry.get(rel, {}).items():
            found.add(target)
            try:
                digest = _pointer(data, pointer)
            except (KeyError, TypeError, IndexError):
                issue("MISSING_REQUIRED_BINDING", rel, pointer)
            else:
                check_edge(rel, target, digest, True)
        geometry = None
        if rel == "analysis/final_validation/input/geometry_manifest.json":
            geometry = data
        elif rel == "analysis/final_validation/results/v0.8/summary.json":
            geometry = data.get("geometry", {})
        if geometry is not None and not isinstance(geometry, dict):
            issue("INVALID_GEOMETRY_ARTIFACT", rel)
            geometry = {}
        if geometry is not None:
            parts = geometry.get("parts", [])
            if not isinstance(parts, list) or not parts:
                issue("MISSING_GEOMETRY_ARTIFACTS", rel)
                parts = []
            names = set()
            for part in parts:
                if not isinstance(part, dict) or not isinstance(part.get("file"), str):
                    issue("INVALID_GEOMETRY_ARTIFACT", rel)
                    continue
                name = part["file"]
                if PurePosixPath(name).name != name:
                    issue("INVALID_GEOMETRY_ARTIFACT", rel, name)
                    continue
                names.add(name)
                target = "analysis/final_validation/input/" + name
                found.add(target)
                check_edge(rel, target, part.get("sha256"), False)
            if not {"bearing_plate.step", "extruder_barrel.step"} <= names:
                issue("MISSING_GEOMETRY_ARTIFACTS", rel)
        if rel == report:
            if not found:
                issue("EMPTY_ROOT_MANIFEST", rel)
            for missing in sorted(set(required_sources) - found):
                issue("MISSING_REQUIRED_SOURCE", rel, missing)
        active.remove(rel)
        reports.add(rel)
    visit(report)
    for rel, expected in tuple(snapshots.items()):
        content = read(rel, report)
        if content is not None and hashlib.sha256(content).hexdigest() != expected:
            issue("CHANGED_DURING_AUDIT", report, rel)
    return {"status": "CURRENT" if not issues else "STALE_OR_INVALID",
            "report": report, "checked_reports": len(reports),
            "checked_files": len(snapshots), "edges": edges, "issues": issues,
            "scope": "declared transitive dependency integrity, not physical validity"}

def evidence_current(root: Path, report: str, required_sources=()) -> bool:
    return audit_evidence(root, report, required_sources)["status"] == "CURRENT"
