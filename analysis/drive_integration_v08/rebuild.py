"""Rebuild only the selected drive package with explicit success evidence."""
from pathlib import Path
import os,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
FC='/nix/store/1lh14ikhjd0jgwngiik411g6blv43bq8-freecad-1.1.3/bin/freecadcmd'

def main():
    result=[]
    for script,marker in [('cache_source.py','SOURCE_CAPTURE_COMPLETE'),('run_generate.py','GENERATED'),('render_geometry.py','CAD_RENDER_DONE')]:
        log=HERE/'raw'/('final_'+script+'.log')
        proc=subprocess.run([FC,str(ROOT/'cad/freecad/drive_v08'/script)],cwd=ROOT,
          env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=600)
        text=proc.stdout+'\n'+proc.stderr;log.write_text(text)
        if proc.returncode or marker not in text or 'Exception while processing' in text:
            raise RuntimeError(script+' failed; see '+str(log))
        result.append({'script':script,'log':str(log.relative_to(ROOT)),
          'sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'status':'EXECUTED'})
    (HERE/'build_execution.json').write_text(json.dumps({'runs':result,'physical_validation':'NOT_RUN'},indent=2)+'\n')
    print('DRIVE_PACKAGE_GEOMETRY_REBUILT')
if __name__=='__main__':main()
