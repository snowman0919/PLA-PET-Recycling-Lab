"""Export the selected v0.8 geometry for engineering review, not fabrication approval."""
from pathlib import Path
import sys,json,hashlib,importlib.util,shutil,csv
import FreeCAD as App,Part,importDXF
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'cad/freecad/compact'))
from geometry import shredder_metal_parts
from cad.freecad.compact.generate import normalize_step,normalize_dxf

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def export_shape(name,shape,folder):
    if not shape.isValid() or not shape.Solids:raise RuntimeError(name+' invalid source')
    path=folder/(name+'.step');shape.exportStep(str(path));normalize_step(path)
    imported=Part.read(str(path));err=abs(imported.Volume-shape.Volume)/max(shape.Volume,1e-12)
    if not imported.isValid() or len(imported.Solids)!=len(shape.Solids) or err>1e-7:raise RuntimeError(name+' STEP roundtrip failed')
    b=shape.BoundBox
    return {'part_id':name,'file':path.name,'solid_count':len(shape.Solids),'bbox_mm':[b.XLength,b.YLength,b.ZLength],'volume_mm3':shape.Volume,'roundtrip_relative_volume_error':err,'sha256':sha(path),'artifact_status':'VALID_GEOMETRY_REVIEW_ONLY','fabrication_state':'HOLD'}

def main():
    out=ROOT/'exports/review/engineering-closure-20260909';stepdir=out/'01_STEP';draw=out/'02_DRAWINGS'
    stepdir.mkdir(parents=True,exist_ok=True);draw.mkdir(parents=True,exist_ok=True)
    specs=[s for s in shredder_metal_parts() if s['id'] in ('CUT-05','CUT-05R')]
    rows=[]
    for s in specs:
        row=export_shape(s['id'],s['shape'],stepdir)
        doc=App.newDocument(s['id'].replace('-','_'));ob=doc.addObject('PartDesign::Feature','Part');ob.Shape=s['shape'];doc.recompute()
        importDXF.export([ob],str(draw/(s['id']+'.dxf')));normalize_dxf(draw/(s['id']+'.dxf'));doc.saveAs(str(stepdir/(s['id']+'.FCStd')));App.closeDocument(doc.Name)
        row['manufacturing_notes']={k:v for k,v in s.items() if isinstance(v,(str,int,float))}
        rows.append(row)
    spec=importlib.util.spec_from_file_location('closure_final_geometry',ROOT/'cad/freecad/final_v08/generate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    objects=module.final_objects()
    assembly=Part.makeCompound([x['shape'] for x in objects])
    rows.append(export_shape('PPR-ASSEMBLY-REVIEW',assembly,stepdir))
    for name in ['ExtruderFixedCollar','ExtruderRearFixedDatum','ExtruderFrontSlidingGuide','ExtruderRearRetainer']:
        rows.append(export_shape(name,next(o['shape'] for o in objects if o['name']==name),stepdir))
    sources=[Path(__file__).resolve(),ROOT/'cad/freecad/compact/geometry.py',ROOT/'cad/freecad/compact/manufacturing.py',ROOT/'cad/freecad/final_v08/generate.py',ROOT/'cad/parameters/baseline.json',ROOT/'cad/parameters/final_v08.json']
    report={'status':'ENGINEERING_REVIEW_ONLY','machine_release_state':'HOLD','physical_validation_state':'NOT_RUN','rows':rows,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources}}
    (out/'geometry_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with (out/'component_review_BOM.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['part_id','quantity','material','state'])
        for s in specs:w.writerow([s['id'],s['qty'],s['material'],'REVIEW_ONLY_NOT_APPROVED'])
    print('CLOSURE_GEOMETRY_REVIEW_READY',len(rows),flush=True)
if __name__=='__main__':main()
