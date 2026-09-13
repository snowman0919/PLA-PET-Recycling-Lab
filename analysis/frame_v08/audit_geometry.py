"""Audit the small frame delta using actual FreeCAD solids and contact distances."""
import hashlib
import json
import sys
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'cad/freecad/drive_v08')]
from cad.freecad.drive_v08.assembly import integrated_objects
from cad.freecad.final_v08.generate import final_objects
from cad.freecad.drive_v08.frame_revision import apply_revision, steel_tie, CONTRACT
OUT = ROOT/'analysis/frame_v08/results'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def native_id(name): return name.replace('.', '_').replace('-', '_')
def profiles(items):
    rows=[]
    for row in items:
        b=row['shape'].BoundBox; dims=[b.XLength,b.YLength,b.ZLength]
        axis=max(range(3),key=dims.__getitem__)
        section=sorted(round(dims[i],6) for i in range(3) if i!=axis)
        if section not in ([20.,20.],[20.,40.]): continue
        if not ('profile' in row['material'].lower() or row['group']=='frame'): continue
        if abs(row['shape'].Volume/(dims[0]*dims[1]*dims[2])-1)>1e-6: continue
        rows.append({'id':native_id(row['name']),'source_object':row['name'],'axis':axis,
          'section_mm':section,'length_mm':round(dims[axis],6),
          'box':[round(v,6) for v in (b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)]})
    return sorted(rows,key=lambda r:r['id'])

def contacts(rows, items):
    by={native_id(r['name']):r['shape'] for r in items}; names={r['id'] for r in rows}
    for row in rows:
        s=by[row['id']]; row['contacts']=[]
        for name,t in by.items():
            if name==row['id']: continue
            sb,tb=s.BoundBox,t.BoundBox
            gaps=[max(0,getattr(sb,x+'Min')-getattr(tb,x+'Max'),getattr(tb,x+'Min')-getattr(sb,x+'Max')) for x in ('X','Y','Z')]
            if sum(v*v for v in gaps)>0.0001: continue
            distance=s.distToShape(t)[0]
            if distance<=0.001: row['contacts'].append({'id':name,'gap_mm':distance,'profile':name in names})
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=json.loads(CONTRACT.read_text()); before,_=integrated_objects(final_objects(), frame_revision=False)
    after,_=apply_revision(before); original={r['name']:r for r in before}
    for r in after:
        if r['name'] in original: assert r['shape'] is original[r['name']]['shape']
    a=profiles(before); b=profiles(after)
    reference=json.loads((ROOT/'docs/reviews/s0-prestart-20260912/frame_profile_evidence.json').read_text())
    assert {r['id'] for r in a}=={r['object'] for r in reference['members']}
    for r in reference['members']:
        live=next(x for x in a if x['id']==r['object'])
        assert abs(live['length_mm']-r['nominal_length_mm'])<1e-6
    totals={}
    for key, section in [('2020',[20.,20.]),('2040',[20.,40.])]:
        rr=[r for r in b if r['section_mm']==section]
        totals[key]={'count':len(rr),'length_mm':sum(r['length_mm'] for r in rr)}
    assert totals==spec['expected_profiles']
    tie,section=steel_tie(spec['tie']); collisions=[]; support=[]
    for row in after:
        if row['name']==spec['tie']['object']: continue
        s=row['shape']
        if tie.BoundBox.intersect(s.BoundBox):
            overlap=tie.common(s).Volume
            if overlap>1e-5: collisions.append([row['name'],overlap])
        if row['name'] in ('FrameY0_0','FrameY0_450'):
            distance=tie.distToShape(s)[0]; support.append([row['name'],distance]); assert distance<1e-7
    assert not collisions,collisions
    for x in spec['tie']['hole_x_mm']:
        for y in spec['tie']['hole_y_local_mm']:
            washer=Part.makeCylinder(spec['tie']['washer_od_mm_max']/2,1,
              App.Vector(x,y+spec['tie']['origin_mm'][1],spec['tie']['origin_mm'][2]+3))
            assert tie.common(washer).Volume<1e-6, 'washer must seat flat outside bend radii'
    a=contacts(a,before); b=contacts(b,after)
    c=tie.BoundBox
    channel={'id':spec['tie']['object'],'source_object':spec['tie']['object'],'axis':0,
      'length_mm':spec['tie']['length_mm'],'box':[c.XMin,c.YMin,c.ZMin,c.XMax,c.YMax,c.ZMax],
      'section_properties':{'area_mm2':section.Area,'iy_mm4':section.MatrixOfInertia.A22,
      'iz_mm4':section.MatrixOfInertia.A33,'j_mm4':section.Area*spec['tie']['thickness_mm']**2/3,'e_mpa':200000,
      'j_basis':'Thin-wall open-section approximation A*t^2/3; not polar inertia or solid torsion qualification',
      'centroid_yz_mm':[section.CenterOfMass.y,section.CenterOfMass.z]}}
    b=contacts([*b,channel],after)
    paths=[Path(__file__).resolve(),CONTRACT,ROOT/'cad/freecad/drive_v08/assembly.py',ROOT/'cad/freecad/drive_v08/frame_revision.py']
    paths += sorted((ROOT/'cad/freecad/drive_v08').glob('*.py'))
    paths += sorted((ROOT/'cad/freecad/compact').glob('*.py'))
    paths += [ROOT/rel for rel in ('cad/freecad/compact/geometry.py','cad/freecad/compact/manufacturing.py',
      'cad/freecad/final_v08/generate.py','cad/parameters/final_v08.json','cad/parameters/baseline.json',
      'docs/reviews/s0-prestart-20260912/frame_profile_evidence.json')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    result={'status':'FRAME_DELTA_GEOMETRY_PASS','source_sha256':hashes,'before':a,'after':b,
      'totals':totals,'removed':spec['remove_profiles'],'unchanged_retained_objects':len(after)-1,
      'new_interferences':collisions,'tie_support_distances':support,'tie_volume_mm3':tie.Volume,
      'physical_validation_state':'NOT_RUN','joint_strength_qualified':False}
    (OUT/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FRAME_DELTA_GEOMETRY_PASS',totals,'unchanged',len(after)-1,'section',channel['section_properties'])

if __name__=='__main__': main()
