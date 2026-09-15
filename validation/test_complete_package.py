"""Offline path, policy, tamper and missing-file rejection unit tests."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('complete',ROOT/'release/verify_complete_release.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
class CompletePackageTest(unittest.TestCase):
 def fixture(self,root):
  files={name:b'fixture' for name in M.REQUIRED}
  data={'schema_version':1,'release_tag':'v1.0.0-rc1','source_commit':'a'*40,
   'release_state':'FABRICATION_CANDIDATE','physical_validation_state':'NOT_RUN',
   'safety_certification_state':'NOT_CERTIFIED','fabrication_authorized':False,'energization_authorized':False,
   'files':[{'path':n,'size':len(v),'sha256':M.sha(v)} for n,v in sorted(files.items())]}
  for n,v in files.items():
   p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
  (root/M.MANIFEST).write_text(json.dumps(data));return data
 def test_paths_fail_closed(self):
  for p in ('../outside','/absolute','a/../b','a//b','a\\b','C:/bad','./a','a\n'):
   with self.subTest(path=p),self.assertRaises(ValueError):M.safe_name(p)
 def test_no_physical_authorization(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'.build') as td:
   d=self.fixture(Path(td));M.validate_metadata(d)
   for k,v in [('energization_authorized',True),('fabrication_authorized','false'),('physical_validation_state','PASS'),('source_commit','bad')]:
    bad=copy.deepcopy(d);bad[k]=v
    with self.assertRaises(ValueError):M.validate_metadata(bad)
 def test_duplicate_and_missing_entries_rejected(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'.build') as td:
   d=self.fixture(Path(td));bad=copy.deepcopy(d);bad['files'].append(bad['files'][0])
   with self.assertRaises(ValueError):M.validate_metadata(bad)
   d['files'].pop()
   with self.assertRaises(ValueError):M.validate_metadata(d)
 def test_tamper_and_extra_file_rejected(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'.build') as td:
   root=Path(td);self.fixture(root)
   with patch.object(M,'validate_contents'):
    self.assertEqual(M.verify(root)['status'],'COMPLETE_PACKAGE_VERIFY_PASS')
    (root/'extra.txt').write_text('extra')
    with self.assertRaises(ValueError):M.verify(root)
    (root/'extra.txt').unlink();(root/'START_HERE.html').write_text('changed')
    with self.assertRaises(ValueError):M.verify(root)
if __name__=='__main__':
 (ROOT/'.build').mkdir(exist_ok=True);unittest.main()
