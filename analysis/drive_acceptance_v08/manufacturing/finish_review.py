"""Verify scoped manufacturing outputs and distinguish numerical checks from permission."""
from pathlib import Path
import json,hashlib,subprocess,math,csv
H=Path(__file__).resolve().parent;R=H.parents[2];O=R/'exports/final/drive_ggm_v08/manufacturing_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(record):
    d=record['source_sha256'];assert d,'empty binding'
    for name,value in d.items():assert sha(R/name)==value,'stale '+name
manifest=json.loads((O/'drawing_manifest.json').read_text());bind(manifest)
cad=json.loads((O.parent/'manifest.json').read_text());bind(cad)
expected={r['file'].replace('.step','').replace('Screw-GGM','Screw').replace('ThrustPlate-GGM','ThrustPlate') for r in cad['exports'] if r['file'] not in ('GGM-FULL-ASM.step','GGM-DRIVE-ASM.step')}
assert expected==set(manifest['covered_objects']),'orphan manufacturing part'
for row in manifest['pages']:assert sha(O/row['file'])==row['sha256'],'changed drawing'
for p in O.glob('*.dxf'):assert 'SECTION' in p.read_text(errors='replace'),'invalid DXF'
info={}
for filename,pages in [('PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf',23),('PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf',5)]:
    text=subprocess.run(['pdfinfo',str(O/filename)],capture_output=True,text=True,check=True).stdout
    actual=int(next(l for l in text.splitlines() if l.startswith('Pages:')).split(':')[1]);assert actual==pages
    info[filename]={'pages':actual,'sha256':sha(O/filename)}
physical=json.loads((H/'physical_record_status.json').read_text())
assert all(v['status']=='NOT_RUN' for v in physical['domains'].values())
q=json.loads((H/'retention_strength_quadratic.json').read_text());bind(q)
regional=json.loads((H/'regional_stress.json').read_text());bind(regional)
rows=[]
for label in ('before','r2'):
    cases=sorted([c for c in q['cases'] if c['revision']==label],key=lambda c:-c['size_mm'])
    m,f=cases[-2:];u=lambda r:r['solver']['max_displacement_mm'];s=lambda r:r['solver']['max_von_mises_mpa']
    rows.append({'variant':label,'medium_to_fine_displacement_fraction':abs(u(m)/u(f)-1),'medium_to_fine_peak_stress_fraction':abs(s(m)/s(f)-1),
       'fine_displacement_mm':u(f),'fine_peak_stress_mpa':s(f),'max_reaction_error':max(c['reaction_error'] for c in cases)})
result={'status':'MANUFACTURING_DOCUMENT_SET_VERIFIED_NOT_MACHINE_RELEASE',
 'drawing_families':manifest['drawing_families'],'drawing_pages':len(manifest['pages']),
 'manufactured_objects_covered':len(expected),'dxf_projections':len(list(O.glob('*.dxf'))),'pdfs':info,
 'physical_validation':'NOT_RUN','physical_domains':physical['domains'],'machine_release':'HOLD',
 'cad_new_interference':cad['review']['new_interference'],'quadratic_plate_cases':len(q['cases']),
 'cold_plate_comparison':rows,'peak_stress_convergence':'DIAGNOSTIC_BOUNDARY_PEAK_NOT_RELEASE_METRIC',
 'plate_displacement_convergence_pass':all(r['medium_to_fine_displacement_fraction']<.02 for r in rows),
 'regional_stress_convergence_pass':regional['convergence_pass'],
 'regional_stress':{'fine_max_mpa':regional['fine_regional_max_mpa'],'fine_p95_mpa':regional['fine_regional_p95_mpa'],'yield_screen_sf':regional['regional_max_yield_screen_sf'],'medium_to_fine':regional['medium_to_fine']},
 'minimum_rear_web_from_drawing_mm':12.00-9.15-.35,
 'limits':['Rigid-boundary nodal peaks remain diagnostic; the explicitly bounded load-path web is the converged cold local stress metric',
 'No whole-joint preload/contact/hot-strength approval is inferred from the cold regional screen',
 'No received motor, alignment, pin or current physical record available',
 'No machining, energization, firmware upload, purchase, push or merge',
 'Drawings express project fit requirements, not measured supplier guarantees'],
 'source_sha256':{str(p.relative_to(R)):sha(p) for p in [Path(__file__).resolve(),H/'drawing_contract.json',H/'inspection.py',
 H/'mesh_quadratic.py',H/'geometry_checks.json',H/'retention_strength_quadratic.json',H/'regional_stress.json',H/'regional_stress_review.py',O/'drawing_manifest.json',H/'physical_record_status.json']}}
(H/'closeout.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','drawing_families','drawing_pages','manufactured_objects_covered','cold_plate_comparison')},ensure_ascii=False,indent=2))
