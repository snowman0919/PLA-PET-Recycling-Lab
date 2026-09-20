"""Validate exported STEP topology and volume, not physical performance."""
from pathlib import Path
import json
import cadquery as cq
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'results/cad_parts.json').read_text())['parts']
checks=[]
for p in a:
    s=cq.importers.importStep(str(R/'cad/parts'/(p['part_id']+'.step'))).val()
    rel=abs(s.Volume()-p['volume_mm3'])/max(1,p['volume_mm3'])
    ok=s.isValid() and len(s.Solids())==1 and rel<1e-5
    checks.append({'part':p['part_id'],'valid':s.isValid(),'solids':len(s.Solids()),'relative_volume_difference':rel,'passed':ok})
s=cq.importers.importStep(str(R/'cad/PPR_C1_assembly.step')).val()
out={'scope':'STEP round trip topology and volume only; no physical qualification','parts':checks,'part_count':len(checks),'assembly_valid':s.isValid(),'assembly_solids':len(s.Solids()),'passed':all(p['passed'] for p in checks) and s.isValid() and len(s.Solids())==199}
(R/'results/step_roundtrip.json').write_text(json.dumps(out,indent=2)+'\n')
print('STEP_ROUNDTRIP',out['passed'],len(checks),out['assembly_solids'],flush=True)
if not out['passed']:
    print([p for p in checks if not p['passed']])
    raise SystemExit(1)
