"""Package a tested prototype snapshot; no fabrication/energization approval."""
import hashlib,json,subprocess,sys,zipfile,tempfile,io,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    reports=['solver_result.json','gradient_result.json']
    cases=[]
    for name in reports:
        data=json.loads((ROOT/name).read_text())
        for path,expected in data['source_sha256'].items():
            assert sha(ROOT/path)==expected,('stale prototype source',name,path)
        for row in data['runs']:
            folder=ROOT/row['raw_directory']
            assert 'JOB FINISHED' in (folder/'ccx.log').read_text().upper()
            assert sha(folder/'model.inp')==row['input_sha256']
            cases.append(folder)
    assert len(cases)==18
    raw={str(p.relative_to(ROOT)):sha(p) for folder in cases for p in folder.iterdir() if p.is_file() and p.suffix in {'.inp','.frd','.dat','.log'}}
    (ROOT/'raw_result_hashes.json').write_text(json.dumps(raw,indent=2))
    test=json.loads((ROOT/'protocol_test_results.json').read_text());assert test['status']=='PASS' and test['count']==26
    bridge=json.loads((ROOT/'geometry_bridge.json').read_text());assert bridge['status']=='PASS'
    for name,expected in bridge['sha256'].items():assert sha(ROOT/name)==expected
    allowed={'.py','.json','.md','.csv','.typ','.txt'}
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in allowed and p.name not in {'package_manifest.json','package_final_check.json'}]
    paths.append(ROOT/'HS-R1-S2_prototype_review_ko_v2.pdf')
    for name in ('fixture','drawings','prototype_geometry_slotted','relief_candidate'):
        paths += [p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix.lower() in {'.step','.fcstd','.dxf','.svg','.json','.md','.brep'}]
    paths=sorted(set(paths));assert all(p.is_file() and p.stat().st_size for p in paths)
    assert all(p.name!='.env' and p.suffix.lower() not in {'.ttf','.otf','.ttc'} for p in paths)
    payload={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    manifest={'status':'PRESSURELESS_PROTOTYPE_REVIEW','variant':'HS-R1-S2','machine_release':'HOLD','physical_validation':'NOT_RUN','source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'successful_selected_solver_runs':18,'raw_files_hashed':len(raw),'algebraic_corner_cases':6144,'free_expansion_pair_checks':48,'unit_tests':26,'geometry_bridge':bridge,'files':{name:{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)} for name,data in payload.items()}}
    payload['package_manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    payload['SHA256SUMS.txt']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(payload.items())).encode()
    def make_zip():
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as archive:
            for name,data in sorted(payload.items()):
                info=zipfile.ZipInfo(name,date_time=(2026,9,9,0,0,0));info.external_attr=0o100644<<16
                archive.writestr(info,data)
        return buf.getvalue()
    first=make_zip();second=make_zip();assert first==second
    archive=REPO/'dist/PPR-HS-R1-S2-TEST-FOUNDATION-20260909.zip';archive.parent.mkdir(exist_ok=True);archive.write_bytes(first)
    with tempfile.TemporaryDirectory(prefix='hs-r1-extract-') as tmp:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for info in z.infolist():
                target=(Path(tmp)/info.filename).resolve()
                assert target.is_relative_to(Path(tmp).resolve())
            z.extractall(tmp)
        for name,data in payload.items():
            assert sha(Path(tmp)/name)==hashlib.sha256(data).hexdigest()
    for name,row in manifest['files'].items():assert sha(ROOT/name)==row['sha256'],('changed during packaging',name)
    (ROOT/'package_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result={'status':'PROTOTYPE_PACKAGE_INTEGRITY_PASS','machine_release':'HOLD','physical_validation':'NOT_RUN','archive':str(archive.relative_to(REPO)),'sha256':sha(archive),'bytes':archive.stat().st_size,'payload_files':len(manifest['files']),'selected_solver_jobs':len(cases),'raw_files_hashed':len(raw),'unit_tests':test['count'],'same_snapshot_two_zip_builds_identical':True,'clean_extraction_verified':True,'complete_pipeline_twice_regenerated':False}
    (ROOT/'package_final_check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
