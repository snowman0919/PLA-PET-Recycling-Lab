"""A publication approval cannot be repurposed as physical approval."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'release'))
from publication_policy import validate_policy
class PublicationPolicyTest(unittest.TestCase):
    def test_authorized_prerelease(self):
        validate_policy(json.loads((ROOT/'release/publication_policy.json').read_text()))
    def test_physical_and_publication_mutations_fail(self):
        original = json.loads((ROOT/'release/publication_policy.json').read_text())
        for key, value in {'publication_kind':'STABLE', 'tag':'v1.0.0', 'fabrication_authorized':True,
                           'energization_authorized':True, 'production_authorized':True,
                           'merge_authorized':True, 'physical_validation_state':'PASS',
                           'safety_certification_state':'CERTIFIED', 'publication_authorized':'true'}.items():
            with self.subTest(key=key):
                policy=deepcopy(original);policy[key]=value
                with self.assertRaises(ValueError):validate_policy(policy)
if __name__=='__main__':unittest.main()
