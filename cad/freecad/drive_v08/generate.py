"""Generate hash-bound GGM drive assets without replacing historical releases."""
from pathlib import Path
import sys,json,hashlib,csv,math
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent))
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.compact.generate import normalize_step,normalize_zip_container,_projection_polylines
from assembly import integrated_objects
from layout import load_base
from validation.integrated_assembly_clearance import audit as audit_integrated
from validation.integrated_motion_clearance import audit as audit_motion
OUT=ROOT/'exports/final/drive_ggm_v08'; OUT.mkdir(parents=True,exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def export(name,items):
    doc=App.newDocument('GGM_'+name.replace('-','_')); features=[]
    for row in items:
        obj=doc.addObject('PartDesign::Feature',row['name']);obj.Shape=row['shape']
        for key,prop in (('name','SourceObjectId'),('classification','ComponentRole'),('material','MaterialSpecification'),('group','Subsystem')):
            obj.addProperty('App::PropertyString',prop,'Handoff');setattr(obj,prop,row[key])
        features.append(obj)
    doc.recompute();path=OUT/(name+'.step');Part.export(features,str(path));normalize_step(path)
    native=OUT/(name+'.FCStd');native.unlink(missing_ok=True);doc.saveAs(str(native));App.closeDocument(doc.Name)
    normalize_zip_container(native,normalize_fcstd=True)
    re=Part.read(str(path));volume=sum(r['shape'].Volume for r in items)
    solids=sum(len(r['shape'].Solids) for r in items)
    if not re.isValid() or len(re.Solids)!=solids or abs(re.Volume-volume)>max(1e-5,volume*1e-6):raise RuntimeError('STEP drift:'+name)
    b=re.BoundBox
    return dict(file=path.name,sha256=sha(path),fcstd=native.name,fcstd_sha256=sha(native),solids=solids,
                volume_mm3=re.Volume,bbox_mm=[b.XLength,b.YLength,b.ZLength],status='REIMPORT_PASS')

def audit(items,changed,base):
    source={r['name']:r for r in base}; new=[]; inherited=[]; simplified=[]
    for i,a in enumerate(items):
        for b in items[i+1:]:
            x,y=a['name'],b['name']
            if x not in changed and y not in changed:continue
            if not a['shape'].BoundBox.intersect(b['shape'].BoundBox):continue
            volume=a['shape'].common(b['shape']).Volume
            if volume<.01:continue
            entry=[x,y,round(volume,5)]
            if x in source and y in source and abs(source[x]['shape'].common(source[y]['shape']).Volume-volume)<.001:
                inherited.append(entry);continue
            bolt=next((n for n in (x,y) if n.startswith(('HotMountBolt','GGM_M5_'))),None)
            rail=next((n for n in (x,y) if n in {'MidRail320','GGM_HotRearRail','GGM_ExMotorRail'}),None)
            if bolt and rail:simplified.append(entry)
            else:new.append(entry)
    return dict(new_interference=new,inherited_findings=inherited,profile_tslot_lod_contacts=simplified)

def drawing(row):
    s=row['shape']; b=s.BoundBox
    view=_projection_polylines(s,('x','z'),(25,90,720,440))
    import html
    title=html.escape(row['name']);material=html.escape(row['material'])
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><rect width="800" height="600" fill="white"/><g font-family="sans-serif" fill="#172533"><text x="25" y="35" font-size="21">{title}</text><text x="25" y="62" font-size="12">{material}</text>{view}<text x="25" y="552" font-size="14">Envelope {b.XLength:.3f} x {b.YLength:.3f} x {b.ZLength:.3f} mm</text><text x="25" y="580" font-size="12">STEP and DRIVE_DRAWING_SCHEDULE.csv control. Physical commissioning not performed.</text></g></svg>'
    (OUT/(row['name']+'.svg')).write_text(svg)

def main():
    paths=list(Path(__file__).resolve().parent.glob('*.py'))+[ROOT/'control/ggm_drive_contract.json', ROOT/'cad/parameters/ggm_frame_revision.json', ROOT/'validation/integrated_assembly_clearance.py', ROOT/'validation/integrated_motion_clearance.py', ROOT/'validation/shaft_retention_clearance.py']
    base_paths=json.loads((ROOT/'analysis/drive_integration_v08/raw/source/manifest.json').read_text())['source_sha256']
    for p,h in base_paths.items():
        if sha(ROOT/p)!=h:raise RuntimeError('Refresh source cache before generation: '+p)
    bindings={str(p.relative_to(ROOT)):sha(p) for p in paths}|base_paths
    base=load_base();items,changed=integrated_objects(base)
    integrated_review=audit_integrated(items)
    motion_review=audit_motion(items)
    review=audit(items,changed,load_base())
    custom=[r for r in items if r['name'].startswith('GGM_') and r['classification']=='manufactured_or_stock']
    rows=[export('GGM-FULL-ASM',items),export('GGM-DRIVE-ASM',[r for r in items if r['name'].startswith('GGM_')])]
    for row in custom:
        rows.append(export(row['name'],[row]));drawing(row)
    for name in ('Screw','ThrustPlate'):
        rows.append(export(name+'-GGM',[r for r in items if r['name']==name]))
    result={'status':'NEW_DRIVE_CLEARANCE_PASS' if not review['new_interference'] else 'NEW_INTERFERENCE_FOUND',
            'machine_release':'HOLD','physical_validation':'NOT_RUN','review':review,'integrated_clearance':integrated_review,'integrated_motion':motion_review,'exports':rows,'source_sha256':bindings,
            'motor_envelopes_not_internals':True,'standard_sprockets_are_reference_envelopes_not_cutting_masters':True}
    if any(sha(ROOT/p)!=h for p,h in bindings.items()):raise RuntimeError('Source changed during generation')
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in items:r['shape'].exportBrep(str(ROOT/'analysis/drive_integration_v08/raw'/(r['name']+'.brep')))
    (ROOT/'analysis/drive_integration_v08/raw/render_items.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='shape'} for r in items]))
    print('GENERATED',len(rows),'NEW_COLLISIONS',review['new_interference'],flush=True)
    if review['new_interference']:raise RuntimeError('Resolve new drive collisions')
if __name__=='__main__':main()
