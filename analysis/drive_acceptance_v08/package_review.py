"""Package the current GGM drive snapshot; never label it a machine release."""
from pathlib import Path
import hashlib, json, subprocess, tempfile, zipfile
from verify_snapshot import check_bindings, bound_path, sha
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
CAD=ROOT/'exports/final/drive_ggm_v08'; DIST=ROOT/'dist'

def gather():
    payload={}
    def add(path,target):
        if target in payload: raise ValueError('Duplicate payload '+target)
        if not path.is_file(): raise ValueError('Missing '+str(path))
        payload[target]=path
    reports=[CAD/'manifest.json', HERE/'acceptance.json', HERE/'geometry_review.json',
        HERE/'process_limits.json', HERE/'firmware_review.json', HERE/'inventory_evidence.json']
    for path in reports: check_bindings(json.loads(path.read_text()))
    geometry=json.loads((CAD/'manifest.json').read_text())
    if geometry['review']['new_interference']: raise ValueError('New interference')
    add(HERE/'CLOSEOUT_KO.md','00_START_HERE/READ_FIRST_KO.md')
    add(HERE/'pdf_status.json','00_START_HERE/pdf_status.json')
    for row in geometry['exports']:
        for filekey,hashkey in [('file','sha256'),('fcstd','fcstd_sha256')]:
            source=bound_path(CAD,row[filekey])
            if sha(source)!=row[hashkey]: raise ValueError('Stale CAD '+source.name)
            add(source,'01_CAD/'+source.name)
        view=CAD/(Path(row['file']).stem+'.svg')
        if view.is_file(): add(view,'02_DRAWING_VIEWS/'+view.name)
    for name in ['GGM_full_layout.png','GGM_shredder_detail.png','GGM_extruder_detail.png','GGM_drive_details.png']:
        add(CAD/name,'02_DRAWING_VIEWS/'+name)
    add(HERE/'drive_component_register.csv','03_BOM/drive_component_register.csv')
    firmware=json.loads((HERE/'firmware_review.json').read_text())
    sketch=CAD/'firmware/arduino_mega'
    for p in sketch.rglob('*'):
        if p.is_file() and p.suffix in ('.h','.cpp','.ino'):
            add(p,'04_FIRMWARE/source/'+str(p.relative_to(sketch)))
    binary=bound_path(ROOT,firmware['hex_path'])
    if sha(binary)!=firmware['hex_sha256']: raise ValueError('HEX changed')
    add(binary,'04_FIRMWARE/GGM_arduino_mega.hex')
    add(CAD/'firmware/manifest.json','04_FIRMWARE/source_manifest.json')
    for p in HERE.glob('*.json'):
        if p.name not in ('package_evidence.json','final_check.json'):
            add(p,'05_EVIDENCE/'+p.name)
    add(CAD/'manifest.json','05_EVIDENCE/cad_manifest.json')
    for name in ('engineering.json','test_result.json'):
        p=ROOT/'analysis/drive_integration_v08'/name
        if p.is_file(): add(p,'05_EVIDENCE/integration_'+name)
    source_paths=set(geometry['source_sha256'])
    source_paths.update(firmware['source_sha256'])
    source_paths.update(str(p.relative_to(ROOT)) for p in HERE.glob('*.py'))
    source_paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'firmware/ggm_drive_v08').glob('*.py'))
    source_paths.add('cad/freecad/compact/generate.py')
    for rel in sorted(source_paths):
        add(bound_path(ROOT,rel),'06_SOURCE_SNAPSHOT/'+rel)
    for name in ('LICENSE','LICENSE-HARDWARE'):
        if (ROOT/name).is_file(): add(ROOT/name,'LICENSES/'+name)
    return payload

def encoded_manifest(payload):
    return {name:{'sha256':sha(p),'bytes':p.stat().st_size,
                  'source_path':str(p.relative_to(ROOT))} for name,p in sorted(payload.items())}

def write_zip(path,payload,manifest):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        entries={name:p.read_bytes() for name,p in payload.items()}
        entries['00_START_HERE/RELEASE_MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
        entries['00_START_HERE/SHA256SUMS.txt']=''.join(
            f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name,data in sorted(entries.items())).encode()
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo('PPR-GGM-DRIVE-REVIEW/'+name,(2000,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            z.writestr(info,data)

def main():
    payload=gather(); hashes=encoded_manifest(payload)
    state={'package_class':'DRIVE_INTEGRATION_REVIEW','machine_release':'HOLD',
        'physical_validation':'NOT_RUN','hardware_authorization':'NOT_GRANTED',
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_snapshot':'Exact files including declared pre-existing uncommitted CAD inputs; not clean-clone reproduction',
        'drawings':'Projection review views; not a complete manufacturing drawing set',
        'pdf':'NOT_CREATED; remote renderer sandbox unavailable',
        'payload':hashes}
    DIST.mkdir(exist_ok=True)
    target=DIST/'PPR-GGM-DRIVE-REVIEW-20260909-r1.zip'
    with tempfile.TemporaryDirectory(prefix='ggm-package-',dir=HERE/'raw') as tmp:
        first=Path(tmp)/'first.zip'; second=Path(tmp)/'second.zip'
        write_zip(first,payload,state); write_zip(second,payload,state)
        if sha(first)!=sha(second): raise RuntimeError('Nonrepeatable ZIP assembly')
        if encoded_manifest(payload)!=hashes: raise RuntimeError('Source changed while packaging')
        extracted=Path(tmp)/'extracted'
        with zipfile.ZipFile(first) as z:
            if z.testzip() is not None: raise RuntimeError('ZIP CRC failure')
            for entry in z.namelist():
                if not (extracted/entry).resolve().is_relative_to(extracted.resolve()):
                    raise ValueError('Unsafe archive entry')
            z.extractall(extracted)
        for name,info in hashes.items():
            if sha(extracted/'PPR-GGM-DRIVE-REVIEW'/name)!=info['sha256']:
                raise RuntimeError('Extraction hash mismatch')
        if target.exists() and sha(target)!=sha(first):
            raise FileExistsError('Preserve prior package; choose a new revision')
        if not target.exists(): target.write_bytes(first.read_bytes())
    report={'status':'PACKAGE_SNAPSHOT_VERIFIED','zip_path':str(target.relative_to(ROOT)),
        'sha256':sha(target),'bytes':target.stat().st_size,'payload_files':len(hashes),
        'same_snapshot_double_zip_match':True,'extraction_hashes_match':True,
        'physical_validation':'NOT_RUN','machine_release':'HOLD',
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'acceptance.json',HERE/'firmware_review.json']}}
    (HERE/'package_evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
