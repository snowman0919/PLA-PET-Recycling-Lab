"""Rebuild only this study with its recorded OpenModelica toolchain."""
from pathlib import Path
import hashlib, json, os, subprocess
HERE=Path(__file__).resolve().parent
FILTER='tempC|readyAt|stage|shredTorqueNm|screwTorqueNm|shredOmega|screwOmega|flowGph|accumulatedG|energyJ|shSquare|exSquare|shTime|exTime|pressureTorqueNm|viscousTorqueNm|diePressurePa|hydraulicLowerTorqueNm|shPeak|heaterW|processTime'
def main():
    config=json.loads((HERE/'runtime.json').read_text())
    for key in ('omc','loader'):
        if not Path(config[key]).is_file(): raise RuntimeError('Recorded runtime missing: '+key)
    raw=HERE/'raw';raw.mkdir(exist_ok=True)
    mos='loadFile('+json.dumps(str(HERE/'SequenceDemand.mo'))+');\ngetErrorString();\n'
    mos+='buildModel(SequenceDemand,stopTime=1800,numberOfIntervals=36000,tolerance=1e-7,method="dassl",outputFormat="csv",variableFilter='+json.dumps(FILTER)+');\ngetErrorString();\n'
    (raw/'build.mos').write_text(mos)
    p=subprocess.run([config['omc'],str(raw/'build.mos')],cwd=raw,capture_output=True,text=True,timeout=180,env=dict(os.environ,OMP_NUM_THREADS='1'))
    log=p.stdout+'\n'+p.stderr;(raw/'build_latest.log').write_text(log)
    if p.returncode or 'Error:' in log or not (raw/'SequenceDemand').is_file(): raise RuntimeError(log[-3000:])
    result={'status':'COMPILED_NOT_PROCESS_VALIDATED','omc_version':config['version'],'model_sha256':hashlib.sha256((HERE/'SequenceDemand.mo').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256((raw/'SequenceDemand').read_bytes()).hexdigest(),'log_sha256':hashlib.sha256((raw/'build_latest.log').read_bytes()).hexdigest()}
    (HERE/'build_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
