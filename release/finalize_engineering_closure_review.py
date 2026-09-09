"""Source-bound review package. Never publishes or declares fabrication approval."""
from pathlib import Path
import csv, hashlib, io, json, sys, tempfile, zipfile
ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'exports/review/engineering-closure-20260909'
REVIEW = ROOT / 'docs/reviews/design-load-closure-20260909'
sys.path.insert(0, str(ROOT / 'validation'))
from evidence_freshness import audit_evidence

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')

def safe_path(rel):
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT) or not p.is_file():
        raise ValueError('Missing or unsafe source: ' + rel)
    return p

def main():
    reports = [
        'analysis/final_validation/results/v0.8/solid_load_path_closure.json',
        'analysis/final_validation/results/v0.8/journal_keyseat_closure/result.json',
        'analysis/final_validation/results/v0.8/thermal_mating_closure/result.json',
    ]
    audits = [audit_evidence(ROOT, rel) for rel in reports]
    if any(a['status'] != 'CURRENT' for a in audits):
        raise RuntimeError('Input evidence has changed; rerun instead of relabeling')
    geometry = json.loads((PACK / 'geometry_manifest.json').read_text())
    for row in geometry['rows']:
        p = PACK / '01_STEP' / row['file']
        if digest(p) != row['sha256'] or row['solid_count'] < 1:
            raise RuntimeError('Geometry mismatch: ' + row['file'])
    solid, journal, hot = [json.loads(safe_path(rel).read_text()) for rel in reports]
    if len(solid['runs']) != 18 or any(r['equilibrium_pass'] is not True for r in solid['runs']):
        raise RuntimeError('Incomplete load-case execution')
    if journal['status'] != 'PASS' or len(hot['cases']) != 48:
        raise RuntimeError('Incomplete journal/thermal check')
    raw_files, finished = {}, 0
    for row in solid['runs']:
        base = safe_path(row['raw_dir'] + '/model.inp').parent
        for name, field in [('model.inp','deck_sha256'), ('model.frd','frd_sha256'), ('model.dat','dat_sha256')]:
            if digest(base/name) != row[field]:
                raise RuntimeError('Stale raw evidence: '+str(base/name))
        text = (base/'ccx.log').read_text(errors='replace')
        if 'JOB FINISHED' not in text.upper():
            raise RuntimeError('Solver completion missing')
        finished += 1
        for p in base.iterdir():
            if p.is_file(): raw_files[str(p.relative_to(ROOT))] = digest(p)
    inputs = {}
    for a in audits:
        for edge in a['edges']: inputs[edge['target']] = edge['actual']
    for rel, expected in geometry.get('source_sha256', {}).items():
        if digest(safe_path(rel)) != expected: raise RuntimeError('Geometry source changed')
        inputs[rel] = expected
    source_roots = ['cad/freecad/compact', 'cad/freecad/final_v08']
    for folder in source_roots:
        for p in (ROOT/folder).glob('*.py'): inputs[str(p.relative_to(ROOT))] = digest(p)
    for rel in ['release/export_engineering_closure_review.py', str(Path(__file__).resolve().relative_to(ROOT)),
                'validation/test_load_path_closure.py','analysis/final_validation/run_calculix_v08.py',
                'analysis/structural/run_load_checks.py','analysis/final_validation/beam_torque_recovery.py',
                'validation/evidence_freshness.py','analysis/final_validation/contracts/thermomechanical_closure_v08.json']:
        inputs[rel] = digest(safe_path(rel))
    ev = PACK / '04_EVIDENCE'; ev.mkdir(exist_ok=True)
    aliases = ['solid_load_path_closure.json','journal_keyseat_closure.json','thermal_mating_closure.json']
    for rel, name in zip(reports, aliases): (ev/name).write_bytes(safe_path(rel).read_bytes())
    contract = 'analysis/final_validation/contracts/thermomechanical_closure_v08.json'
    (ev/'thermomechanical_closure_v08.json').write_bytes(safe_path(contract).read_bytes())
    (ev/'final_unit_tests.json').write_bytes((REVIEW/'final_unit_tests.json').read_bytes())
    dump(ev/'source_freshness.json', audits)
    dump(ev/'raw_result_hashes.json', {'scope':'Original-machine evidence, large raw files not bundled', 'files':raw_files})
    dump(ev/'input_sources.json', {'source_sha256':inputs})
    for rel, expected in inputs.items():
        p=safe_path(rel)
        if p.suffix in {'.py','.json','.step','.md','.csv'}:
            target=PACK/'05_SOURCE'/rel; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(p.read_bytes())
    shaft_rows = [r for r in geometry['rows'] if r['part_id'] in {'CUT-05','CUT-05R'}]
    with (PACK/'component_review_BOM.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=['part_id','quantity','material','process','critical','step_file','step_sha256','state'])
        writer.writeheader()
        for row in shaft_rows:
            note=row['manufacturing_notes']
            writer.writerow({'part_id':row['part_id'],'quantity':note['qty'],'material':note['material'],
                'process':note['process'],'critical':note['critical'],'step_file':'01_STEP/'+row['file'],
                'step_sha256':row['sha256'],'state':'ENGINEERING_REVIEW_ONLY_FABRICATION_HOLD'})

    (PACK/'README_KO.md').write_text((REVIEW/'README_KO.md').read_text() + '\n## Package use\nThis is an engineering review, not a fabrication release. Read 03_DOCUMENTS/closure_review_ko_20260909.pdf first. component_review_BOM.csv covers only the two changed shafts. 05_SOURCE is a related-source snapshot, not a standalone distribution of the entire repository. Large raw solver outputs remain on the original machine and are hash-bound in 04_EVIDENCE/raw_result_hashes.json. Review and analysis STEP files may differ in export metadata; each has its own hash and reimport-volume check.\n',encoding='utf-8')
    payload = [p for p in PACK.rglob('*') if p.is_file() and p.name not in {'review_manifest.json','SHA256SUMS.txt'}]
    if any(p.name == '.env' or p.suffix in {'.ttf','.otf','.ttc'} for p in payload): raise RuntimeError('Forbidden payload')
    files={str(p.relative_to(PACK)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(payload)}
    manifest={'schema_version':1,'package_state':'ENGINEERING_REVIEW_ONLY','machine_release_state':'HOLD',
        'physical_validation_state':'NOT_RUN','geometry_entries':len(geometry['rows']),
        'finished_solid_solver_jobs':finished,'thermal_pair_checks':len(hot['cases']),
        'thermal_interference_states':hot['interference_count'],'source_sha256':inputs,'files':files}
    dump(PACK/'review_manifest.json',manifest)
    all_files=sorted(p for p in PACK.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
    (PACK/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+str(p.relative_to(PACK))+'\n' for p in all_files))
    def zip_bytes():
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as archive:
            for p in sorted(p for p in PACK.rglob('*') if p.is_file()):
                info=zipfile.ZipInfo(str(p.relative_to(PACK)),date_time=(2026,9,9,0,0,0))
                info.external_attr=0o100644<<16
                archive.writestr(info,p.read_bytes())
        return buffer.getvalue()
    first=zip_bytes(); second=zip_bytes()
    if first!=second:raise RuntimeError('Nondeterministic packaging of identical snapshot')
    out=ROOT/'dist/PPR-v08-engineering-review-20260909.zip';out.parent.mkdir(exist_ok=True)
    out.write_bytes(first)
    with tempfile.TemporaryDirectory(prefix='ppr-review-extract-') as temp:
        with zipfile.ZipFile(out) as archive:
            if archive.testzip() is not None:raise RuntimeError('ZIP CRC error')
            archive.extractall(temp)
        for rel,row in files.items():
            if digest(Path(temp)/rel)!=row['sha256']:raise RuntimeError('Extracted hash mismatch')
    for rel,expected in inputs.items():
        if digest(safe_path(rel))!=expected:raise RuntimeError('Source changed during packaging')
    final={'status':'REVIEW_PACKAGE_INTEGRITY_PASS','machine_release_state':'HOLD',
        'zip':str(out.relative_to(ROOT)),'zip_sha256':digest(out),'zip_bytes':out.stat().st_size,
        'payload_files':len(files),'source_files':len(inputs),'solid_solver_jobs':finished,
        'raw_files_hashed':len(raw_files),'thermal_pair_checks':len(hot['cases']),
        'thermal_interference_states':hot['interference_count'],
        'same_snapshot_two_zip_builds_identical':True,'full_pipeline_twice_regenerated':False,
        'clean_extraction_verified':True,'source_freshness':[a['status'] for a in audits]}
    dump(REVIEW/'final_check.json',final)
    print(json.dumps(final,indent=2))

if __name__=='__main__':main()
