#!/usr/bin/env python3
"""Promote the verified GGM drive R2 review into the final manufacturing family."""
from pathlib import Path
import csv, hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'exports/final/drive_ggm_v08'
MFG=SRC/'manufacturing_r2'
OUT=ROOT/'exports/final/manufacturing/drive_ggm'
REG=ROOT/'analysis/drive_acceptance_v08/drive_component_register.csv'
CONTRACT=ROOT/'analysis/drive_acceptance_v08/manufacturing/drawing_contract.json'
CLOSE=ROOT/'analysis/drive_acceptance_v08/manufacturing/closeout.json'
REV='final-design-fabrication-closure-v0.8'
SUPERSEDED={'DRV-01','DRV-02','DRV-A60','DRV-F01A','DRV-F01B','DRV-F01P'}
ALIASES={'Screw':'EX-SCR-01','ThrustPlate':'EX-THR-01'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def source_step(obj):
    if obj=='Screw': return SRC/'Screw-GGM.step'
    if obj=='ThrustPlate': return SRC/'ThrustPlate-GGM.step'
    return SRC/f'{obj}.step'
def main():
    close=json.loads(CLOSE.read_text(encoding='utf-8'))
    assert close['status']=='MANUFACTURING_DOCUMENT_SET_VERIFIED_NOT_MACHINE_RELEASE'
    assert close['regional_stress_convergence_pass'] is True and close['machine_release']=='HOLD'
    contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
    register={r['cad_object']:r for r in read_csv(REG)}
    drawing_for={obj:part for part in contract['parts'] for obj in part['objects']}
    covered=set(json.loads((MFG/'drawing_manifest.json').read_text())['covered_objects'])
    assert covered==set(drawing_for)
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy2(MFG/'PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf',OUT/'PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf')
    shutil.copy2(MFG/'PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf',OUT/'PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf')
    fields=['part_id','revision','quantity','material','process','critical_tolerance','datum_scheme','inspection','status','step_file','dxf_file','drawing_pdf','sha256_step','sha256_dxf','sha256_pdf','release_gate']
    rows=[]
    for obj in sorted(covered):
        reg=register[obj]; part=drawing_for[obj]; pid=ALIASES.get(obj,obj)
        step_src=source_step(obj); dxf_src=MFG/f"{part['id']}.dxf"
        assert step_src.is_file() and dxf_src.is_file()
        step=OUT/f'{pid}.step'; dxf=OUT/f'{pid}.dxf'
        shutil.copy2(step_src,step); shutil.copy2(dxf_src,dxf)
        notes='; '.join(part['notes'])
        rows.append({'part_id':pid,'revision':REV,'quantity':reg['quantity'],'material':reg['material_note'],
            'process':part['process'],'critical_tolerance':notes,
            'datum_scheme':f"drawing {part['id']} axis {part['axis']}; coordinates/features govern",
            'inspection':'PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf + drawing notes; receipt/alignment/pin/current physical domains NOT_RUN',
            'status':'PASS','step_file':step.name,'dxf_file':dxf.name,
            'drawing_pdf':'PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf',
            'sha256_step':sha(step),'sha256_dxf':sha(dxf),
            'sha256_pdf':sha(OUT/'PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf'),
            'release_gate':'DIGITAL_DRIVE_DESIGN_PASS_PHYSICAL_NOT_RUN'})
    # Canonical EX-SCR/EX-THR rows are delta drawings, not additional quantities.
    ids=[r['part_id'] for r in rows]
    assert len(ids)==len(set(ids)) and len(rows)==39
    with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    meta={'revision':REV,'status':'PASS','rows':len(rows),'physical_validation':'NOT_RUN','machine_release':'HOLD',
          'supersedes_legacy_part_ids':sorted(SUPERSEDED),
          'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (REG,CONTRACT,CLOSE,MFG/'drawing_manifest.json',MFG/'PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf')}}
    (OUT/'release_report.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    update_active(rows)
    print(f"V08_GGM_DRIVE_RELEASE_OK rows={len(rows)} legacy_removed={len(SUPERSEDED)}")
def update_active(ggm_rows):
    print_rows=read_csv(ROOT/'exports/final/print/print_manifest.csv')
    rfq_rows=read_csv(ROOT/'exports/final/manufacturing/RFQ/manifest.csv')
    parts={f'PPR-{name}-ASM':1 for name in ('FULL','SHREDDER','FEEDER','EXTRUDER','FORMING','FRAME')}
    for r in print_rows+rfq_rows+ggm_rows:
        pid=r['part_id']; qty=int(r['quantity'])
        if pid in SUPERSEDED: continue
        if pid in parts and parts[pid]!=qty: raise ValueError(f'quantity conflict {pid}')
        parts[pid]=qty
    register={r['part_id']:r for r in read_csv(REG)}
    for pid in ('GGM_SH_12T','GGM_SH_30T'):
        r=register[pid]
        if r['classification']!='purchased_reference_envelope': raise ValueError(pid+' is no longer a purchased sprocket reference')
        parts[pid]=int(r['quantity'])
    active={'revision':REV,'state':'FABRICATION_CANDIDATE','physical_validation_state':'NOT_RUN',
            'parts':[{'part_id':pid,'quantity':qty} for pid,qty in sorted(parts.items())]}
    (ROOT/'release/active_part_set.json').write_text(json.dumps(active,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
