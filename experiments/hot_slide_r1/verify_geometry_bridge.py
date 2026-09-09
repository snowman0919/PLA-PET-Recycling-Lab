"""Bind solver geometry to the separately exported prototype manufacturing body."""
from pathlib import Path
import json,hashlib
import FreeCAD as App,Part
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    names=['prototype_geometry_slotted/HS-R1-sheet.step','fixture/HS-R1-SHEET.step']
    shapes=[Part.read(str(ROOT/name)) for name in names]
    assert all(s.isValid() and len(s.Solids)==1 and s.Volume>0 for s in shapes)
    difference=shapes[0].cut(shapes[1]).Volume+shapes[1].cut(shapes[0]).Volume
    relative=abs(shapes[0].Volume-shapes[1].Volume)/shapes[0].Volume
    assert difference<1e-5 and relative<1e-6
    result={'status':'PASS','scope':'Same BRep geometry in solver STEP and prototype manufacturing STEP; not a physical load rating','symmetric_volume_difference_mm3':difference,'relative_volume_error':relative,'physical_validation':'NOT_RUN','sha256':{name:sha(ROOT/name) for name in names},'verifier_sha256':sha(Path(__file__))}
    (ROOT/'geometry_bridge.json').write_text(json.dumps(result,indent=2)+'\n')
    print('GEOMETRY_BRIDGE_PASS',difference,relative,flush=True)
if __name__=='__main__':main()
