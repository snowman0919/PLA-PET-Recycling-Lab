"""Check changed solids against current layout without reclassifying old overlaps."""
from pathlib import Path
import sys,json
import FreeCAD as App
import Part
sys.path.insert(0,str(Path(__file__).resolve().parent))
from layout import ROOT
from assembly import integrated_objects as layout
out=ROOT/'analysis/drive_integration_v08/raw'
items,changed=layout(); conflicts=[]
for i,a in enumerate(items):
    for b in items[i+1:]:
        if a['name'] not in changed and b['name'] not in changed: continue
        if not a['shape'].BoundBox.intersect(b['shape'].BoundBox): continue
        c=a['shape'].common(b['shape'])
        if c.Volume>0.01: conflicts.append([a['name'],b['name'],round(c.Volume,4)])
compound=Part.makeCompound([i['shape'] for i in items]); b=compound.BoundBox
report={'conflicts':conflicts,'bbox':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],'changed':changed}
(out/'layout_probe.json').write_text(json.dumps(report,indent=2))
compound.exportBrep(str(out/'layout_probe.brep'))
print('LAYOUT_PROBE',json.dumps(report),flush=True)
