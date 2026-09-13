"""Capture current source solids for scoped GGM integration checks."""
from pathlib import Path
import sys, json, hashlib
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from cad.freecad.final_v08.generate import final_objects
OUT=ROOT/'analysis/drive_integration_v08/raw/source'
OUT.mkdir(parents=True,exist_ok=True)
paths=sorted((ROOT/'cad/freecad/compact').glob('*.py'))+sorted((ROOT/'cad/freecad/final_v08').glob('*.py'))+[Path(__file__).resolve(),ROOT/'cad/parameters/final_v08.json',ROOT/'cad/parameters/baseline.json']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
items=final_objects()
rows=[]
for item in items:
    s=item['shape']; s.exportBrep(str(OUT/(item['name']+'.brep')))
    row={k:v for k,v in item.items() if k!='shape'}
    b=s.BoundBox; row['bbox']=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
    row['volume']=s.Volume
    row['brep_sha256']=hashlib.sha256((OUT/(item['name']+'.brep')).read_bytes()).hexdigest()
    rows.append(row)
if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
    raise RuntimeError('Source changed during source capture')
(OUT/'manifest.json').write_text(json.dumps({'objects':rows,'source_sha256':hashes,'freecad':App.Version()},indent=2))
print('SOURCE_CAPTURE_COMPLETE',len(rows),flush=True)
