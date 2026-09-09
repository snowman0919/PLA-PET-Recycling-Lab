"""Drive-only object register from the exported native assembly, not purchase orders."""
from pathlib import Path
import csv, hashlib, json, re
import FreeCAD as App
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
OUT=ROOT/'exports/final/drive_ggm_v08'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    native=OUT/'GGM-FULL-ASM.FCStd'
    metadata=ROOT/'analysis/drive_integration_v08/raw/render_items.json'
    hashes={str(p.relative_to(ROOT)):sha(p) for p in (native,metadata,Path(__file__))}
    doc=App.openDocument(str(native)); rows=[]
    for item in json.loads(metadata.read_text()):
        name=item['name']
        if not(name.startswith('GGM_') or name in ('Screw','ThrustPlate') or name.startswith('SpoolTopSegment')): continue
        obj=doc.getObject(name) or doc.getObject(re.sub(r'[^A-Za-z0-9_]', '_', name))
        if obj is None: raise ValueError('Object missing '+name)
        box=obj.Shape.BoundBox
        exported=name if name.startswith('GGM_') else name+'-GGM'
        step=OUT/(exported+'.step')
        rows.append(dict(part_id=name,cad_object=obj.Name,quantity=1,classification=item['classification'],
            material_note=item['material'],bbox_mm=' x '.join(f'{v:.3f}' for v in (box.XLength,box.YLength,box.ZLength)),
            local_step=step.name if step.is_file() else 'GGM-FULL-ASM.step component',
            purchasing='CHECK_EXISTING_STOCK_FIRST',status='DRIVE_DELTA_REVIEW_ONLY'))
    App.closeDocument(doc.Name)
    if any(sha(ROOT/p)!=h for p,h in hashes.items()): raise RuntimeError('Assembly changed')
    with (HERE/'drive_component_register.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    result={'row_count':len(rows),'count_is_not_unique_buy_items':True,
        'source_sha256':hashes, 'component_register_sha256':sha(HERE/'drive_component_register.csv'),
        'physical_validation':'NOT_RUN','machine_release':'HOLD'}
    (HERE/'inventory_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('DRIVE_INVENTORY',len(rows))

main()
