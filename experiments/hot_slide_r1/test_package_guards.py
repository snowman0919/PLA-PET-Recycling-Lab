"""Isolated packaging mutations; never change the working prototype record."""
import tempfile, shutil, json, subprocess, sys
from pathlib import Path
E=Path(__file__).resolve().parent
results=[]
with tempfile.TemporaryDirectory(prefix='hs-package-mutation-') as temporary:
    copy=Path(temporary)/'experiments/hot_slide_r1'
    shutil.copytree(E,copy,ignore=shutil.ignore_patterns('raw_runs','raw','source_cache','measurements','pdf_preview','__pycache__','cache','*.log'))
    (copy/'raw_runs').symlink_to(E/'raw_runs',target_is_directory=True)
    (copy/'qualification/raw').symlink_to(E/'qualification/raw',target_is_directory=True)
    record=copy/'physical_test_template.json'; original=record.read_bytes()
    data=json.loads(original);data['performed']=True;record.write_text(json.dumps(data))
    proc=subprocess.run([sys.executable,str(copy/'package_review.py')],cwd=copy,capture_output=True,text=True,timeout=90)
    assert proc.returncode!=0 and 'Refuse to package measured data' in proc.stderr
    results.append({'mutation':'performed_template','status':'REJECTED'})
    record.write_bytes(original)
    path=copy/'solver_result.json'; data=json.loads(path.read_text())
    key=next(iter(data['source_sha256']));data['source_sha256'][key]='0'*64
    path.write_text(json.dumps(data))
    proc=subprocess.run([sys.executable,str(copy/'package_review.py')],cwd=copy,capture_output=True,text=True,timeout=90)
    assert proc.returncode!=0 and 'stale prototype source' in proc.stderr
    results.append({'mutation':'stale_solver_source','status':'REJECTED'})
assert json.loads((E/'physical_test_template.json').read_text())['performed'] is False
report={'status':'PASS','kind':'SYNTHETIC_MUTATIONS_ONLY','tests':results,'physical_validation':'NOT_RUN'}
Path(__file__).with_name('package_guard_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
