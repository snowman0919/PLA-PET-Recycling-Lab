#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
BANNED=('EX-SCR-01','EX-BAR-01','gate1_powered_assembly','DRV-01','DRV-Axx','DRV-F01')
REQUIRED=('00_READ_FIRST/STATUS.json','00_EXECUTION/PHYSICAL_EXECUTION_INDEX_KO.md','00_EXECUTION/physical_gate_contract.json','02_ANALYZERS/analyze_ggm_mount_compatibility.py','02_ANALYZERS/analyze_p1_records.py','02_ANALYZERS/analyze_p2_records.py','02_ANALYZERS/build_p3_inspection_packet.py','03_P4_GATE1/gate1_assembly.step','04_P4_CNC/CUT-01/CUT-01.step','05_P5_COUPONS/EX-CPN-SCR/EX-CPN-SCR.step','05_P5_COUPONS/EX-CPN-BAR/EX-CPN-BAR.step','06_P3_GGM/manifest.csv','MANIFEST.sha256')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('zip',type=Path);a=ap.parse_args();root=Path(__file__).resolve().parents[2]
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 with zipfile.ZipFile(a.zip) as z:
  names=z.namelist(); dup=[n for n in set(names) if names.count(n)>1]
  if dup: raise SystemExit('duplicate zip paths')
  if any(any(b in n for b in BANNED) for n in names): raise SystemExit('banned production/legacy path present')
  for n in REQUIRED:
   if n not in names: raise SystemExit('missing '+n)
  status=json.loads(z.read('00_READ_FIRST/STATUS.json'))
  if status.get('package_state')!='PREPARATION_ONLY_NOT_FABRICATION_AUTHORIZATION': raise SystemExit('wrong package state')
  if status.get('head')!=head: raise SystemExit('package HEAD is stale')
  for k in ('procurement_authorized','motor_energization_authorized','heater_energization_authorized'):
   if status.get(k) is not False: raise SystemExit(k+' must be false')
  manifest={}
  for line in z.read('MANIFEST.sha256').decode().splitlines():
   digest,name=line.split('  ',1); manifest[name]=digest
  for name,digest in manifest.items():
   if name not in names: raise SystemExit('manifest path missing '+name)
   if hashlib.sha256(z.read(name)).hexdigest()!=digest: raise SystemExit('hash mismatch '+name)
  if set(manifest)!=(set(names)-{'MANIFEST.sha256'}): raise SystemExit('manifest coverage mismatch')
 print(f'PHYSICAL_LAUNCH_PACKAGE_PASS files={len(names)} head={head[:12]} state=PREPARATION_ONLY')
if __name__=='__main__': main()
