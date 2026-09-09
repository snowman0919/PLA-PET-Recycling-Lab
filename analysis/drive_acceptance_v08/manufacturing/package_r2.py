"""Package only verified drive manufacturing data; no physical authorization."""
from pathlib import Path
import json,hashlib,zipfile,tempfile,subprocess
H=Path(__file__).resolve().parent;R=H.parents[2];O=R/'exports/final/drive_ggm_v08'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_bindings(rec):
    for p,h in rec.get('source_sha256',{}).items():
        if sha(R/p)!=h:raise ValueError('stale source '+p)
def main():
    check_bindings(json.loads((O/'manifest.json').read_text()))
    close=json.loads((H/'closeout.json').read_text());check_bindings(close)
    assert close['machine_release']=='HOLD' and close['physical_validation']=='NOT_RUN'
    draw=json.loads((O/'manufacturing_r2/drawing_manifest.json').read_text());check_bindings(draw)
    halves=json.loads((O/'manufacturing_r2/guard_half_manifest.json').read_text());check_bindings(halves)
    payload={}
    def add(path,dest):
        path=Path(path)
        if not path.is_file():raise ValueError('missing '+str(path))
        if any(s in path.name.lower() for s in ('.env','.fcbak','.ttf','.otf','.pem')):raise ValueError('excluded file')
        if dest in payload:raise ValueError('duplicate '+dest)
        payload[dest]=path
    for row in json.loads((O/'manifest.json').read_text())['exports']:
        for field,hashfield in [('file','sha256'),('fcstd','fcstd_sha256')]:
            p=O/row[field];assert sha(p)==row[hashfield];add(p,'01_CAD/'+p.name)
    for p in (O/'manufacturing_r2').iterdir():
        if p.suffix.lower() in {'.pdf','.svg','.dxf','.json','.csv','.typ','.step'}:add(p,'02_DRAWINGS/'+p.name)
    for p in H.iterdir():
        if p.suffix in {'.py','.json','.csv','.md','.typ'}:add(p,'03_METHOD_AND_EVIDENCE/'+p.name)
    add(R/'analysis/drive_acceptance_v08/drive_component_register.csv','04_BOM/drive_component_register.csv')
    add(R/'analysis/drive_acceptance_v08/firmware_review.json','05_FIRMWARE_REFERENCE/firmware_review.json')
    fw=R/'exports/final/drive_ggm_v08/firmware'
    for rel in ('manifest.json','binaries/arduino_mega.ino.hex','arduino_mega/src/ggm_drive_guard.h','arduino_mega/src/ggm_commissioning.h'):
        add(fw/rel,'05_FIRMWARE_REFERENCE/'+rel)
    for p in (R/'cad/freecad/drive_v08').glob('*.py'):add(p,'06_SOURCE/'+str(p.relative_to(R)))
    for p in (R/'cad/freecad/compact').glob('*.py'):add(p,'06_SOURCE/'+str(p.relative_to(R)))
    for name in ['cad/freecad/final_v08/generate.py','cad/parameters/baseline.json','cad/parameters/final_v08.json','control/ggm_drive_contract.json']:
        add(R/name,'06_SOURCE/'+name)
    for name in ('LICENSE','LICENSE-HARDWARE'):
        if (R/name).is_file():add(R/name,'LICENSES/'+name)
    payload={k:v for k,v in payload.items() if v.name not in {'package_evidence.json','final_check.json','commit_record.json'}}
    records={name:{'source_path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for name,p in payload.items()}
    meta={'kind':'MANUFACTURING_REVIEW_NOT_FABRICATION_RELEASE','physical_validation':'NOT_RUN','machine_release':'HOLD',
      'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
      'git_worktree_clean':not subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip(),
      'basis':'Exact file snapshot; pre-existing worktree changes preserved; no clean-clone qualification claimed',
      'files':records}
    extra=json.dumps(meta,ensure_ascii=False,indent=2).encode()
    def write(path):
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,p in sorted(payload.items()):
                entry=zipfile.ZipInfo('PPR-GGM-MFG-r2/'+name,(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(entry,p.read_bytes())
            entry=zipfile.ZipInfo('PPR-GGM-MFG-r2/REVIEW_MANIFEST.json',(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,extra)
    dest=R/'dist/PPR-GGM-MANUFACTURING-REVIEW-20260910-r2.zip'
    with tempfile.TemporaryDirectory(dir=H/'raw') as tmp:
        first=Path(tmp)/'a.zip';second=Path(tmp)/'b.zip';write(first);write(second)
        assert sha(first)==sha(second),'nondeterministic snapshot archive'
        with zipfile.ZipFile(first) as z:
            assert z.testzip() is None;z.extractall(Path(tmp)/'extract')
        for name,p in payload.items():
            assert sha(p)==records[name]['sha256'],'source changed during packaging'
            assert sha(Path(tmp)/'extract/PPR-GGM-MFG-r2'/name)==sha(p),'extraction mismatch'
        dest.write_bytes(first.read_bytes())
    result={'zip_path':str(dest.relative_to(R)),'sha256':sha(dest),'bytes':dest.stat().st_size,'payload_files':len(payload),
        'two_same_snapshot_zips_match':True,'extraction_verified':True,'machine_release':'HOLD','physical_validation':'NOT_RUN'}
    (H/'package_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
