#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PHYS=ROOT/'validation/physical_v08'
DIST=ROOT/'dist'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def add_file(items,src,arc):
 p=ROOT/src
 if not p.is_file(): raise FileNotFoundError(src)
 items.append((p,arc))
def main():
 subprocess.run(['python3',str(PHYS/'simulation_prerequisite.py')],cwd=ROOT,check=True)
 snap=json.loads((PHYS/'simulation_prerequisite.json').read_text())
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if snap.get('status')!='PASS' or snap.get('head')!=head: raise SystemExit('fresh P0 PASS snapshot required')
 items=[]
 core=['PHYSICAL_EXECUTION_INDEX_KO.md','PHYSICAL_BUILD_READINESS_KO.md','physical_gate_contract.json','physical_execution_registry.json','stage_minimum_bom.csv','fabrication_sequence.csv','inventory_confirmation.csv','measurement_equipment.csv','P1_EXECUTION_KO.md','P2_COLD_FIT_KO.md','P3_GGM_BENCH_KO.md','P4_SHREDDER_COUPON_KO.md','P5_PROCESS_COUPON_KO.md','P6_COLD_EXTRUDER_KO.md','P7_ELECTRICAL_SAFETY_KO.md','P8_INSTALLED_MOTOR_DRY_RUN_KO.md','P9_EMPTY_HOT_ZONE_KO.md','P10_P11_MATERIAL_RUN_KO.md','P12_FORMING_SPOOL_KO.md','p3_bench_bom.csv','p3_fixture_contract.json','p5_coupon_contract.json','p5_supplier_inspection_requirements.csv']
 for n in core: add_file(items,f'validation/physical_v08/{n}',f'00_EXECUTION/{n}')
 for p in sorted((PHYS/'templates').iterdir()):
  if p.is_file(): items.append((p,'01_TEMPLATES/'+p.name))
 for p in sorted(PHYS.glob('analyze_*.py'))+[PHYS/'profile_nesting.py',PHYS/'build_p3_inspection_packet.py']:
  if p.is_file(): items.append((p,'02_ANALYZERS/'+p.name))
 gate1=['assembly_ko.md','bom.csv','fastener_schedule.csv','wiring_bom.csv','wiring_24v_hardcut.svg','test_procedure_ko.md','preflight_inspection_template.csv','gate1_results_template.csv','jam_recovery_results_template.csv','chip_size_results_template.csv','drive_calibration_template.csv','calibration_log_template.csv','evidence_manifest_template.csv','gate1_assembly.step']
 for n in gate1: add_file(items,f'exports/jigs/gate1/{n}',f'03_P4_GATE1/{n}')
 for part in ('CUT-01','CUT-03','CUT-04','CUT-05','CUT-05R','CUT-08','CUT-09','CUT-10'):
  for ext in ('.step','.dxf'):
   add_file(items,f'exports/cnc/{part}/{part}{ext}',f'04_P4_CNC/{part}/{part}{ext}')
  add_file(items,f'exports/cnc/{part}/drawing_notes.md',f'04_P4_CNC/{part}/drawing_notes.md')
 for part in ('DRV-03','DRV-03R'):
  for ext in ('.step','.dxf'):
   add_file(items,f'exports/drive_interface/parts/{part}/{part}{ext}',f'04_P4_CNC/{part}/{part}{ext}')
  add_file(items,f'exports/drive_interface/parts/{part}/drawing_notes.md',f'04_P4_CNC/{part}/drawing_notes.md')
 for n in ('EX-CPN_drawing.svg','inspection_report_template.csv','supplier_rfq_checklist_ko.md'):
  add_file(items,f'exports/cnc/extruder/{n}',f'05_P5_COUPONS/{n}')
 for part in ('EX-CPN-SCR','EX-CPN-BAR'):
  for ext in ('.step','.dxf'):
   add_file(items,f'exports/cnc/extruder/parts/{part}/{part}{ext}',f'05_P5_COUPONS/{part}/{part}{ext}')
  add_file(items,f'exports/cnc/extruder/parts/{part}/drawing_notes.md',f'05_P5_COUPONS/{part}/drawing_notes.md')
 gdir=ROOT/'exports/final/manufacturing/drive_ggm'
 for p in sorted(gdir.iterdir()):
  if p.is_file() and (p.name.startswith('GGM_') or p.name in {'manifest.csv','release_report.json'}) and p.suffix in {'.step','.dxf','.csv','.json'}:
   items.append((p,'06_P3_GGM/'+p.name))
 status={'package_state':'PREPARATION_ONLY_NOT_FABRICATION_AUTHORIZATION','head':head,'P0':'PASS','P1_P12':'NOT_RUN','procurement_authorized':False,'motor_energization_authorized':False,'heater_energization_authorized':False,'production_parts_intentionally_excluded':['EX-SCR-01','EX-BAR-01','remaining CUT-01 full stack','legacy DRV-01 powered fixture']}
 readme=('PPR v0.8 physical validation launch package\n\n'+json.dumps(status,ensure_ascii=False,indent=2)+'\n')
 payload={arc:sha(p) for p,arc in items}
 payload['00_READ_FIRST/STATUS.json']=hashlib.sha256((json.dumps(status,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
 payload['00_READ_FIRST/README.txt']=hashlib.sha256(readme.encode()).hexdigest()
 manifest=''.join(f'{payload[k]}  {k}\n' for k in sorted(payload))
 DIST.mkdir(exist_ok=True); out=DIST/f'PPR-v08-PHYSICAL-VALIDATION-LAUNCH-{head[:8]}.zip'
 zi=lambda name: zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p,arc in sorted(items,key=lambda x:x[1]): z.writestr(zi(arc),p.read_bytes())
  z.writestr(zi('00_READ_FIRST/STATUS.json'),(json.dumps(status,ensure_ascii=False,indent=2)+'\n').encode())
  z.writestr(zi('00_READ_FIRST/README.txt'),readme.encode())
  z.writestr(zi('MANIFEST.sha256'),manifest.encode())
 print(json.dumps({'path':str(out),'sha256':sha(out),'files':len(payload)+1,'head':head,'state':status['package_state']}))
if __name__=='__main__': main()
