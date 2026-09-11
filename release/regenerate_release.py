#!/usr/bin/env python3
"""Regenerate distribution artifacts; recorded physics is re-audited, not re-solved."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.build/release-regeneration'
JOBS=[
 ('cad/freecad/final_v08/generate.py',['--refresh-assemblies'],True,'V08_ASSEMBLY_REFRESH_OK'),
 ('release/build_mechanical_release.py',[],True,'V08_MECHANICAL_RELEASE_OK'),
 ('validation/test_native_model_handoff.py',[],True,'GGM_NATIVE_STEP_HANDOFF_PASS'),
 ('release/build_ggm_drive_release.py',[],False,'V08_GGM_DRIVE_RELEASE_OK'),
 ('release/build_electrical_firmware_release.py',[],False,'V08_ELECTRICAL_FIRMWARE_RELEASE_OK'),
 ('release/build_final_documents.py',[],False,'V08_FINAL_DOCUMENTS_OK'),
 ('release/build_bom_release.py',[],False,'V08_BOM_RELEASE_OK'),
 ('release/build_print_release.py',[],False,'V08_PRINT_RELEASE_OK'),
 ('release/render_handoff.py',[],True,'HANDOFF_RENDER_PASS')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);tmp=OUT/'tmp';tmp.mkdir(exist_ok=True)
 env=dict(os.environ,TMPDIR=str(tmp),QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 report={'generation_base_commit':head,'status':'RUNNING','records':[],
  'scope':'Distribution regeneration and native/STEP reimport; no new full FEA/Modelica solve',
  'physical_validation_state':'NOT_RUN','energization_authorized':False}
 for i,(script,args,cad,marker) in enumerate(JOBS):
  command=[sys.executable,script,*args];stdin=None
  if cad:
   command=[shutil.which('FreeCADCmd') or 'FreeCADCmd','-c']
   code=('import os,sys,runpy,traceback\nrc=0\n'+f'sys.argv={[script,*args]!r}\n'+
    f'try:\n runpy.run_path({script!r},run_name="__main__")\n'+
    'except SystemExit as e:\n rc=int(e.code or 0)\nexcept BaseException:\n traceback.print_exc();rc=1\n'+
    'sys.stdout.flush();sys.stderr.flush();os._exit(rc)\n')
   stdin='exec('+repr(code)+')\n'
  log=OUT/f'{i:02d}-{Path(script).stem}.log';t=time.monotonic();print('REGENERATE',script,flush=True)
  with log.open('w') as f:
   try:rc=subprocess.run(command,cwd=ROOT,env=env,input=stdin,text=True,stdout=f,stderr=f,timeout=1800).returncode
   except subprocess.TimeoutExpired:rc=124
  text=log.read_text(errors='replace');passed=rc==0 and marker in text
  report['records'].append({'script':script,'args':args,'returncode':rc,'marker':marker,
   'status':'PASS' if passed else 'FAIL','seconds':round(time.monotonic()-t,3),
   'source_sha256':sha(ROOT/script),'log':str(log.relative_to(ROOT)),'log_sha256':sha(log)})
  report['status']='RUNNING' if passed else 'FAIL';(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
  if not passed:print(text[-6000:]);raise SystemExit('Regeneration failed: '+script)
  print('PASS',script,flush=True)
 report['status']='PASS';(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('RELEASE_REGENERATION_PASS',head,len(report['records']))
if __name__=='__main__':main()
