"""Integrity regression tests; never execute a solver or mutate project evidence."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from evidence_freshness import audit_evidence

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "geometry.py").write_text("version_one")
        self.write("child.json", {"source_sha256": {"geometry.py": self.sha("geometry.py")}})
        self.write("root.json", {"source_sha256": {"child.json": self.sha("child.json")}})
    def sha(self, rel):
        return hashlib.sha256((self.root / rel).read_bytes()).hexdigest()
    def write(self, rel, obj):
        (self.root / rel).write_text(json.dumps(obj))
    def audit(self, **kwargs):
        return audit_evidence(self.root, "root.json", **kwargs)
    def kinds(self, **kwargs):
        return {i["kind"] for i in self.audit(**kwargs)["issues"]}
    def test_valid_chain(self):
        self.assertEqual(self.audit()["status"], "CURRENT")
    def test_transitive_same_size_change(self):
        (self.root / "geometry.py").write_text("version_two")
        self.assertIn("HASH_MISMATCH", self.kinds())
    def test_missing_leaf(self):
        (self.root / "geometry.py").unlink()
        self.assertIn("UNREADABLE_OR_UNSAFE_PATH", self.kinds())
    def test_empty_manifest(self):
        self.write("root.json", {"source_sha256": {}})
        self.assertIn("EMPTY_ROOT_MANIFEST", self.kinds())
    def test_wrong_hash_type(self):
        self.write("root.json", {"source_sha256": {"geometry.py": True}})
        self.assertIn("INVALID_DIGEST", self.kinds())
    def test_missing_required_source(self):
        self.assertIn("MISSING_REQUIRED_SOURCE", self.kinds(required_sources=("new_import.py",)))
    def test_parent_escape(self):
        self.write("root.json", {"source_sha256": {"../outside.py": "0"*64}})
        self.assertIn("UNREADABLE_OR_UNSAFE_PATH", self.kinds())
    def test_absolute_path(self):
        self.write("root.json", {"source_sha256": {str(self.root/"geometry.py"): "0"*64}})
        self.assertIn("UNREADABLE_OR_UNSAFE_PATH", self.kinds())
    def test_bad_json(self):
        (self.root/"child.json").write_text("{")
        self.write("root.json", {"source_sha256": {"child.json": self.sha("child.json")}})
        self.assertIn("INVALID_REPORT_JSON", self.kinds())
    def test_cycle(self):
        self.write("child.json", {"source_sha256": {"root.json": "0"*64}})
        self.write("root.json", {"source_sha256": {"child.json": self.sha("child.json")}})
        self.assertIn("DEPENDENCY_CYCLE", self.kinds())
    def test_unbound_scalar(self):
        self.write("root.json", {"source_sha256": self.sha("geometry.py")})
        self.assertIn("UNBOUND_SCALAR_DIGEST", self.kinds())
    def test_registered_scalar(self):
        self.write("root.json", {"source_sha256": self.sha("geometry.py")})
        result=self.audit(scalar_bindings={"root.json":{"/source_sha256":"geometry.py"}})
        self.assertEqual(result["status"], "CURRENT")
    def test_raw_artifacts_checked(self):
        self.write("root.json", {"artifacts_sha256": {"geometry.py":"0"*64}})
        self.assertIn("HASH_MISMATCH", self.kinds())
    def test_freshness_does_not_promote_hold(self):
        self.write("root.json", {"status":"HOLD", "source_sha256":{"geometry.py":self.sha("geometry.py")}})
        self.assertEqual(self.audit()["status"], "CURRENT")
        self.assertEqual(json.loads((self.root/"root.json").read_text())["status"], "HOLD")
    def test_missing_scalar_binding(self):
        result=self.audit(scalar_bindings={"root.json":{"/geometry/hash":"geometry.py"}})
        self.assertIn("MISSING_REQUIRED_BINDING", {i["kind"] for i in result["issues"]})
    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            leaf=Path(outside)/"foreign"; leaf.write_text("abc")
            (self.root/"escape").symlink_to(leaf)
            self.write("root.json", {"source_sha256":{"escape":hashlib.sha256(b"abc").hexdigest()}})
            self.assertIn("UNREADABLE_OR_UNSAFE_PATH", self.kinds())

    def geometry_audit(self, corrupt=False, missing=False):
        rel="analysis/final_validation/input/geometry_manifest.json"
        folder=self.root/"analysis/final_validation/input";folder.mkdir(parents=True)
        parts=[]
        for name in ("bearing_plate.step","extruder_barrel.step"):
            target=folder/name;target.write_text(name)
            parts.append({"file":name,"sha256":self.sha(str(target.relative_to(self.root)))})
        self.write(rel,{"geometry_source_sha256":self.sha("geometry.py"),"parts":[] if missing else parts})
        if corrupt: (folder/"bearing_plate.step").write_text("changed artifact")
        return audit_evidence(self.root,rel,scalar_bindings={rel:{"/geometry_source_sha256":"geometry.py"}})
    def test_geometry_artifacts_match(self):
        self.assertEqual(self.geometry_audit()["status"],"CURRENT")
    def test_geometry_artifact_mismatch(self):
        self.assertIn("HASH_MISMATCH",{i["kind"] for i in self.geometry_audit(corrupt=True)["issues"]})
    def test_geometry_artifact_missing(self):
        self.assertIn("MISSING_GEOMETRY_ARTIFACTS",{i["kind"] for i in self.geometry_audit(missing=True)["issues"]})

if __name__ == "__main__":
    unittest.main(verbosity=2)
