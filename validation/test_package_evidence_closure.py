"""Missing/stale deep inputs must fail even when outer file hashes are correct."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'release'))
from evidence_closure import validate_evidence_closure

REPORT = 'analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json'
MIDDLE = 'analysis/final_validation/results/v0.8/journal_keyseat_closure/result.json'
LEAF = 'cad/input.txt'


class EvidenceClosureTest(unittest.TestCase):
    def setUp(self):
        base = ROOT / '.build' / 'package-evidence-tests'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put(LEAF, b'geometry-v2')
        self.bind(MIDDLE, LEAF)
        self.bind(REPORT, MIDDLE)
        self.sources = {REPORT, MIDDLE, LEAF}

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def bind(self, parent, target):
        digest = hashlib.sha256((self.root / target).read_bytes()).hexdigest()
        self.put(parent, json.dumps({'source_sha256': {target: digest}}).encode())

    def test_complete_graph(self):
        result = validate_evidence_closure(self.root, self.sources)
        self.assertEqual(result['status'], 'PACKAGED_PHYSICS_DEPENDENCIES_CURRENT')
        self.assertFalse(result['fabrication_authorized'])

    def test_leaf_present_locally_but_not_packaged(self):
        with self.assertRaisesRegex(ValueError, 'unpackaged'):
            validate_evidence_closure(self.root, self.sources - {LEAF})

    def test_middle_present_locally_but_not_packaged(self):
        with self.assertRaisesRegex(ValueError, 'unpackaged'):
            validate_evidence_closure(self.root, self.sources - {MIDDLE})

    def test_fresh_parent_cannot_hide_stale_grandchild(self):
        self.put(LEAF, b'geometry-v3')
        self.bind(REPORT, MIDDLE)
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_evidence_closure(self.root, self.sources)

    def test_missing_physical_leaf(self):
        (self.root / LEAF).unlink()
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_evidence_closure(self.root, self.sources)

    def test_empty_scope_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no declared'):
            validate_evidence_closure(self.root, {LEAF})

    def test_cycle_rejected(self):
        self.put(MIDDLE, json.dumps({'source_sha256': {REPORT: '0'*64}}).encode())
        self.bind(REPORT, MIDDLE)
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_evidence_closure(self.root, self.sources)

    def test_noncanonical_dependency_rejected(self):
        self.put(MIDDLE, json.dumps({'source_sha256': {'../input.txt': '0'*64}}).encode())
        self.bind(REPORT, MIDDLE)
        with self.assertRaisesRegex(ValueError, 'stale'):
            validate_evidence_closure(self.root, self.sources)


if __name__ == '__main__':
    unittest.main()
