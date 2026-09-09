"""Hard-bore relief candidate, usable only with independently centred support.
Never changes the active PPR geometry or approves a load path.
"""
import sys,json,hashlib,copy
from pathlib import Path
import FreeCAD as App,Part
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'cad/freecad/final_v08'))
import generate as final
OUT=HERE/'relief_candidate';OUT.mkdir(exist_ok=True)
def expand(s,a,t):
    v=App.Vector(367,347,382);s=s.copy();s.translate(-v);s.scale(1+a*(t-20));s.translate(v);return s

def main():
    old=copy.deepcopy(final.PARAMS)
    original={r['name']:r['shape'] for r in final.final_objects()}
    final.PARAMS['hot_zone_mount']['fixed_collar_bore_mm']=34.60
    final.PARAMS['rear_axial_retainer']['collar_counterbore_mm']=44.60
    new={r['name']:r['shape'] for r in final.final_objects()}
    new['ExtruderRearRetainer']=new['ExtruderRearRetainer'].cut(Part.makeCylinder(17.30,20,App.Vector(365,347,382),App.Vector(1,0,0))).removeSplitter()
    names=('ExtruderRearFixedDatum','ExtruderFixedCollar','ExtruderFrontSlidingGuide','ExtruderRearRetainer')
    records=[];geometry=[]
    for name in names:
        shape=new[name];assert shape.isValid() and len(shape.Solids)==1
        doc=App.newDocument('HS_'+name);obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape;doc.recompute()
        path=OUT/(name+'.step');Part.export([obj],str(path));back=Part.read(str(path))
        error=abs(back.Volume-shape.Volume)/shape.Volume
        assert back.isValid() and len(back.Solids)==1 and error<1e-6
        App.closeDocument(doc.Name)
        geometry.append({'part':name,'step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'volume_mm3':shape.Volume,'roundtrip_relative_error':error})
    for alpha in (12.3e-6,17e-6):
        for tb in (270,300):
            barrel=expand(original['Barrel'],alpha,tb)
            for ts in (20,100,200):
                for name in names:
                    support=expand(new[name],12e-6,ts)
                    overlap=barrel.common(support).Volume
                    records.append({'part':name,'barrel_c':tb,'support_c':ts,'alpha_per_k':alpha,'overlap_mm3':overlap})
                print('RELIEF_BOUND',alpha,tb,ts,flush=True)
    failures=[r for r in records if r['overlap_mm3']>1e-5]
    result={'status':'NO_INTERFERENCE_IN_DEFINED_BOUND' if not failures else 'INTERFERENCE_REMAINS','machine_release':'HOLD','physical_validation':'NOT_RUN','requires':'HS-R1 or another independently qualified centring mechanism, axial retention requalification and machine integration; never use larger bores alone','test_count':len(records),'interference_count':len(failures),'rows':records,'geometry':geometry,'assumptions':'Free isotropic expansion about the existing datum; no solved temperature/contact/friction field','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),ROOT/'cad/freecad/final_v08/generate.py',ROOT/'cad/freecad/compact/geometry.py',ROOT/'cad/freecad/compact/manufacturing.py',ROOT/'cad/parameters/final_v08.json')}}
    (OUT/'result.json').write_text(json.dumps(result,indent=2))
    final.PARAMS=old
    print('RELIEF_CANDIDATE_DONE',len(records),len(failures),flush=True)
if __name__=='__main__':main()
