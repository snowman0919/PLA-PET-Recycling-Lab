"""Released BRep free-expansion interference audit; no contact stress claim."""
import sys, json, hashlib, os
from pathlib import Path
import FreeCAD as App, Part
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'cad/freecad/final_v08'))
import generate as final

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def expand(shape,alpha,temp,origin):
    result=shape.copy()
    result.translate(-origin)
    result.scale(1+alpha*(temp-20))
    result.translate(origin)
    return result

def main():
    objects={o['name']:o for o in final.final_objects()}
    out=ROOT/'analysis/final_validation/results/v0.8/thermal_mating_closure'
    out.mkdir(parents=True,exist_ok=True)
    contract_path=ROOT/'analysis/final_validation/contracts/thermomechanical_closure_v08.json'
    contract=json.loads(contract_path.read_text())
    names=['ExtruderRearFixedDatum','ExtruderFixedCollar','ExtruderFrontSlidingGuide','ExtruderRearRetainer']
    origin=App.Vector(367,347,382)
    baseline=[]
    barrel=objects['Barrel']['shape']
    reference=ROOT/'analysis/final_validation/results/v0.8/thermal_mating_reference'
    equivalence=[]
    for name in ['Barrel']+names:
        prior=reference/(name+'.brep')
        if prior.exists():
            original=Part.Shape();original.read(str(prior))
            current=objects[name]['shape']
            delta=original.cut(current).Volume+current.cut(original).Volume
            equivalence.append({'part':name,'symmetric_volume_difference_mm3':delta,'reference_sha256':sha(prior),'status':'PASS' if delta<1e-6 else 'FAIL'})
        objects[name]['shape'].exportBrep(str(out/(name+'.brep')))
    for name in names:
        s=objects[name]['shape']
        baseline.append({'part':name,'overlap_mm3':barrel.common(s).Volume,'distance_mm':barrel.distToShape(s)[0]})
    rows=[]
    for alpha in contract['cte_sensitivity_per_k']:
        for tb in contract['barrel_temperature_cases_c']:
            hot=expand(barrel,alpha,tb,origin)
            for ts in contract['support_temperature_cases_c']:
                for name in names:
                    support=expand(objects[name]['shape'],contract['support_cte_sensitivity_per_k'],ts,origin)
                    vol=hot.common(support).Volume
                    rows.append({'part':name,'barrel_temp_c':tb,'support_temp_c':ts,'barrel_alpha_per_k':alpha,'support_alpha_per_k':contract['support_cte_sensitivity_per_k'],'overlap_mm3':vol,'distance_mm':hot.distToShape(support)[0],'status':'INTERFERENCE_IN_FREE_EXPANSION_BOUND' if vol>1e-5 else 'NO_INTERFERENCE_IN_THIS_BOUND'})
                print('HOT_MATING_BOUND',alpha,tb,ts,flush=True)
    result={'status':'HOLD_THERMAL_MOUNT_PAIR_QUALIFICATION','physical_validation_state':'NOT_RUN','method':'uniform free isotropic BRep expansion about rear shoulder X367, axis Y347 Z382; not coupled temperature/contact solution','source_temperature_limits':'design upper300 from baseline; support20/100/200 are sensitivity states, not measured temperatures','baseline':baseline,'cases':rows,'nominal_geometry_equivalence':equivalence,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [contract_path,Path(__file__).resolve(),ROOT/'cad/freecad/final_v08/generate.py',ROOT/'cad/freecad/compact/geometry.py',ROOT/'cad/freecad/compact/manufacturing.py',ROOT/'cad/parameters/final_v08.json',ROOT/'cad/parameters/baseline.json']}}
    result['interference_count']=sum(r['overlap_mm3']>1e-5 for r in rows)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('THERMAL_MATING_DONE',len(rows),result['interference_count'],flush=True)
if __name__=='__main__':main()
