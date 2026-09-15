"""Verify full journal lands and cutter/gear key engagement on both active shafts."""
import sys,math,json,hashlib,os
from pathlib import Path
import FreeCAD as App, Part
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cad/freecad/compact'))
from geometry import cutter_shaft,shredder_metal_parts

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotate(s,a):
    r=s.copy();r.rotate(App.Vector(),App.Vector(0,1,0),a);return r

def main():
    stations=json.loads((ROOT/'analysis/final_validation/input/geometry_manifest.json').read_text())['shredder_stations']
    out=ROOT/'analysis/final_validation/results/v0.8/journal_keyseat_closure';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for sid in ['105','153']:
        st=stations[sid];start=st['shaft_y_min_mm'];phase=25.714 if sid=='153' else 0
        shape=cutter_shaft(key_phase_deg=phase,shaft_id=sid)
        old=cutter_shaft(key_phase_deg=phase,shaft_id='105')
        journals=[]
        for centre in st['bearing_y_mm']:
            local=centre-start
            cylinder=Part.makeCylinder(12.5,12,App.Vector(0,local-6,0),App.Vector(0,1,0))
            missing=cylinder.cut(shape).Volume
            journals.append({'centre_y_mm':centre,'entire_combined_envelope_local_y_mm':[local-6,local+6], 'missing_volume_mm3':missing,'legacy_missing_volume_mm3':cylinder.cut(old).Volume,'status':'PASS' if missing<1e-6 else 'FAIL'})
        keychecks=[]
        for index,centre in enumerate(st['cutter_y_mm']):
            key=rotate(Part.makeBox(6,6,3.4,App.Vector(-3,centre-start-3,9.1)),phase)
            overlap=shape.common(key).Volume
            keychecks.append({'kind':'cutter','index':index,'overlap_mm3':overlap,'status':'PASS' if overlap<1e-6 else 'FAIL'})
        yc=st['gear_y_mm']-start
        # Compare actual axial overlap with key land; legacy slave has 16 of 18 mm.
        key=rotate(Part.makeBox(8,16,3.9,App.Vector(-4,yc-7,8.6)),phase)
        overlap=shape.common(key).Volume
        keychecks.append({'kind':'phase_key_required16mm','overlap_mm3':overlap,'status':'PASS' if overlap<1e-6 else 'FAIL'})
        part='CUT-05R' if sid=='153' else 'CUT-05'
        step=ROOT/'analysis/final_validation/input'/(part+'.step')
        shape.exportStep(str(step));imp=Part.read(str(step))
        check={'valid':imp.isValid(),'solids':len(imp.Solids),'volume_relative_error':abs(imp.Volume-shape.Volume)/shape.Volume}
        assert check['valid'] and check['solids']==1 and check['volume_relative_error']<1e-8
        notes=next(r for r in shredder_metal_parts() if r['id']==part)
        rows.append({'part_id':part,'shaft_id':sid,'journal_checks':journals,'key_checks':keychecks,'step_sha256':sha(step),'step':str(step.relative_to(ROOT)),'step_reimport':check,'volume_mm3':shape.Volume,'legacy_volume_mm3':old.Volume,'status':'PASS' if all(r['status']=='PASS' for r in journals+keychecks) else 'FAIL','drawing_notes':{k:v for k,v in notes.items() if isinstance(v,(str,int,float))}})
    result={'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','scope':'Digital full journal lands and key void axial/clock registration; no fatigue/contact/physical-fit approval','physical_validation_state':'NOT_RUN','rows':rows,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'cad/freecad/compact/geometry.py',ROOT/'cad/freecad/compact/manufacturing.py',ROOT/'analysis/final_validation/input/geometry_manifest.json']}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('JOURNAL_KEYSEAT_CLOSURE',result['status'],flush=True)
if __name__=='__main__':main()
