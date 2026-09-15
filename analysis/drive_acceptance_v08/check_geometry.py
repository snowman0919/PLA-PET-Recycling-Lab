"""Read the exported assembly and independently inspect functional bearing lands."""
from pathlib import Path
import hashlib, json, math
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'exports/final/drive_ggm_v08'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    path = OUT/'GGM-FULL-ASM.FCStd'
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in
        (path, OUT/'manifest.json', ROOT/'control/ggm_drive_contract.json', Path(__file__))}
    report = json.loads((OUT/'manifest.json').read_text())
    if sha(path) != report['exports'][0]['fcstd_sha256']:
        raise ValueError('Native assembly does not match export manifest')
    contract = json.loads((ROOT/'control/ggm_drive_contract.json').read_text())
    doc = App.openDocument(str(path))
    def obj(name):
        item = doc.getObject(name)
        if item is None or not hasattr(item,'Shape'): raise ValueError('Missing '+name)
        return item.Shape
    jack = obj('GGM_SH_Jackshaft'); screw = obj('Screw')
    lands = []
    for name, shape, x, y, z, length in [
        ('jack_front',jack,153,243,676.167,10),
        ('jack_rear',jack,153,273,676.167,10),
        ('screw_radial',screw,320,401,382,10)]:
        cyl = Part.makeCylinder(6,length,App.Vector(x,y,z),App.Vector(0,1,0))
        missing = cyl.cut(shape).Volume
        lands.append({'id':name,'datum':[x,y,z], 'length_mm':length,
                      'missing_round_journal_mm3':missing,'pass':missing<1e-4})
    keypairs = [('GGM_SH_Jackshaft','GGM_SH_JackInputKey'),
        ('GGM_SH_Jackshaft','GGM_SH_JackSprocketKey'),
        ('GGM_Shredder','GGM_SH_MotorKey'),('GGM_Extruder','GGM_EX_MotorKey'),
        ('Screw','GGM_EX_ScrewKey')]
    keys = [{'parts':[a,b], 'intersection_mm3':obj(a).common(obj(b)).Volume}
            for a,b in keypairs]
    pitch = contract['shredder']['chain_pitch_mm']; n1,n2 = contract['shredder']['teeth']
    c = contract['shredder']['chain_center_nominal_mm']
    approx_pitches = 2*c/pitch+(n1+n2)/2+(n2-n1)**2*pitch/(4*math.pi**2*c)
    data = {'status':'BEARING_LAND_AND_KEY_GEOMETRY_REVIEW',
        'physical_validation':'NOT_RUN','machine_release':'HOLD',
        'journal_checks':lands,'key_checks':keys,
        'chain_calculated_pitches':approx_pitches,
        'chain_contract_pitches':contract['shredder']['chain_pitches'],
        'scope':'Nominal CAD; not fits, contact stiffness, tooth profile or fatigue qualification',
        'source_sha256':bindings}
    App.closeDocument(doc.Name)
    if any(sha(ROOT/p)!=h for p,h in bindings.items()): raise RuntimeError('Source changed')
    (HERE/'geometry_review.json').write_text(json.dumps(data,indent=2)+'\n')
    assert all(r['pass'] for r in lands), 'Keyseat crosses bearing land'
    assert all(r['intersection_mm3']<.01 for r in keys), 'Nominal key interference'
    assert abs(approx_pitches-contract['shredder']['chain_pitches'])<.01
    print('GEOMETRY_REVIEW_PASS',len(lands),len(keys),approx_pitches)

main()
