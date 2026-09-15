"""Read-only FreeCAD station audit; no manufacturing geometry changes."""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'cad/freecad/final_v08'))
import generate as final

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    names = ('Barrel', 'ExtruderRearFixedDatum', 'ExtruderFixedCollar',
             'ExtruderFrontSlidingGuide', 'ExtruderRearRetainer', 'ThrustPlate')
    shapes = {item['name']: item['shape'] for item in final.final_objects()}
    rows = []
    for name in names:
        shape = shapes[name]
        if not shape.isValid() or len(shape.Solids) != 1:
            raise ValueError('Invalid controlling solid: ' + name)
        box = shape.BoundBox
        rows.append({'name': name, 'solid_count': 1, 'volume_mm3': shape.Volume,
                     'bbox_mm': [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]})
    sources = [Path(__file__).resolve(), ROOT/'cad/freecad/compact/geometry.py',
               ROOT/'cad/freecad/compact/manufacturing.py', ROOT/'cad/freecad/final_v08/generate.py',
               ROOT/'cad/parameters/final_v08.json', ROOT/'cad/parameters/baseline.json']
    result = {'status': 'READ_ONLY_GEOMETRY_AUDIT', 'physical_validation': 'NOT_RUN',
              'parts': rows, 'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources}}
    (HERE/'geometry.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PRACTICAL_GEOMETRY_AUDIT_DONE', len(rows), flush=True)

if __name__ == '__main__':
    main()
