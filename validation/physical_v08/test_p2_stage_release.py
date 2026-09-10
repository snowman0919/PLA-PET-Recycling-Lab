#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/f'{name}.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

FIX=load('test_p2_execution')
P2=load('analyze_p2_records')
REL=load('validate_p2_stage_release')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def make_release(run:Path):
    record,inventory,packet,stock,approval=FIX.make_fixture(run)
    result=P2.evaluate(record,inventory,packet,stock,2.0,approval)
    assert result['status']=='P2_RECORD_CHECK_PASS'
    result_path=run/'p2_result.json'; result_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    data={
        'stage':'P2','status':'PASS','release_scope':'P2_COLD_FRAME_FIT_COMPLETE_P3_ENTRY_ONLY',
        'approved_by':'ENGINEER-A','independent_reviewer':'REVIEWER-B','reviewed_at':'2026-09-10T23:58:00+09:00',
        'p1_inventory':inventory.name,'p1_inventory_sha256':sha(inventory),
        'ggm_packet':packet.name,'ggm_packet_sha256':sha(packet),
        'profile_stock':stock.name,'profile_stock_sha256':sha(stock),'kerf_budget_mm':2.0,
        'fabrication_approval':approval.name,'fabrication_approval_sha256':sha(approval),
        'p2_record':record.name,'p2_record_sha256':sha(record),
        'p2_result':result_path.name,'p2_result_sha256':sha(result_path),
        'p3_entry_review':True,'p5_entry_review':True,'motor_energization_authorized':False,
        'further_fabrication_authorized':False,'machine_release':'HOLD'}
    release=run/'p2_stage_release.json'; release.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    return release,data,record,inventory,packet,stock,approval,result_path

class P2StageReleaseTest(unittest.TestCase):
    def test_valid_release_revalidates_full_chain(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            release,*_=make_release(Path(td)); result=REL.validate(release)
            self.assertEqual(result['status'],'P2_STAGE_RELEASE_VALIDATED')
            self.assertTrue(result['p3_entry_prerequisite']); self.assertTrue(result['p5_entry_prerequisite'])
            self.assertFalse(result['motor_energization_authorized']); self.assertFalse(result['further_fabrication_authorized'])
    def test_rejects_record_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            release,data,*_=make_release(Path(td)); data['p2_record_sha256']='0'*64
            release.write_text(json.dumps(data)+'\n',encoding='utf-8')
            with self.assertRaises(ValueError): REL.validate(release)
    def test_rejects_tampered_saved_result(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            release,data,record,inventory,packet,stock,approval,result_path=make_release(Path(td))
            saved=json.loads(result_path.read_text()); saved['prerequisites']['kerf_budget_mm']=3.0
            result_path.write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8')
            data['p2_result_sha256']=sha(result_path); release.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
            with self.assertRaises(ValueError): REL.validate(release)

if __name__=='__main__': unittest.main()
