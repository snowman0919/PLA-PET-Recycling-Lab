#!/usr/bin/env python3
import json,tempfile,unittest,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tape',HERE/'validate_thermal_barrier_tape_contract.py'); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
class TapeContractTest(unittest.TestCase):
    def test_current_passes(self): self.assertEqual(M.validate()['status'],'THERMAL_BARRIER_TAPE_CONTRACT_PASS')
    def test_rejects_safety_role(self):
        d=json.loads((HERE.parents[1]/'control/thermal_barrier_tape_contract.json').read_text()); d['safety_role']='PRIMARY_CUTOFF'
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            p=Path(td)/'t.json'; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'safety-role'): M.validate(p)
    def test_rejects_install_authority(self):
        d=json.loads((HERE.parents[1]/'control/thermal_barrier_tape_contract.json').read_text()); d['authorization']['installation_authorized']=True
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            p=Path(td)/'t.json'; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'authorization'): M.validate(p)
if __name__=='__main__': unittest.main()
