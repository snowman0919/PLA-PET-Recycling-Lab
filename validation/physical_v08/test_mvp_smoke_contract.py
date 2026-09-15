#!/usr/bin/env python3
import copy,json,tempfile,unittest,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('smoke',HERE/'validate_mvp_smoke_contract.py'); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
class SmokeContractTest(unittest.TestCase):
    def test_current_contract_passes(self):
        self.assertEqual(M.validate()['status'],'MVP_SMOKE_CONTRACT_PASS')
    def test_rejects_throwaway_mvp(self):
        d=json.loads((HERE/'mvp_smoke_contract.json').read_text()); d['identity']['throwaway_prototype_allowed']=True
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            p=Path(td)/'c.json'; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'throwaway'): M.validate(p)
    def test_rejects_acceptance_relaxation(self):
        d=json.loads((HERE/'mvp_smoke_contract.json').read_text()); d['feedback_loop']['acceptance_relaxation_allowed']=True
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            p=Path(td)/'c.json'; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'fail-closed'): M.validate(p)
if __name__=='__main__': unittest.main()
