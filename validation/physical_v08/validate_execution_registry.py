#!/usr/bin/env python3
from __future__ import annotations
import json,py_compile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def req(ok,msg):
 if not ok: raise AssertionError(msg)

def resolve(rel): return (ROOT/rel).resolve()

def main():
 reg=json.loads((ROOT/'physical_execution_registry.json').read_text()); contract=json.loads((ROOT/'physical_gate_contract.json').read_text())
 expected=[f'P{i}' for i in range(13)]; stages=reg['stages']; ids=[s['id'] for s in stages]
 req(ids==expected,f'stage order mismatch: {ids}')
 policy=reg['policy']
 for k in ('physical_action_authorized','procurement_authorized','motor_energization_authorized','heater_energization_authorized','production_certification'):
  req(policy.get(k) is False,k+' must remain false')
 cby={g['id']:g for g in contract['gates']}; req(set(cby)==set(expected),'contract stage set mismatch')
 for s in stages:
  req(s['name']==cby[s['id']]['name'],s['id']+' name drift')
  req(s['state']=='RUNTIME_EVALUATED' if s['id']=='P0' else s['state']=='NOT_RUN',s['id']+' unexpected state')
  doc=resolve(s['doc']); analyzer=resolve(s['analyzer'])
  req(doc.is_file(),s['id']+' missing doc '+str(doc)); req(analyzer.is_file(),s['id']+' missing analyzer '+str(analyzer))
  if analyzer.suffix=='.py': py_compile.compile(str(analyzer),doraise=True)
  if s.get('preflight_analyzer'):
   preflight=resolve(s['preflight_analyzer']); req(preflight.is_file(),s['id']+' missing preflight analyzer '+str(preflight))
   py_compile.compile(str(preflight),doraise=True)
  if s.get('packet_builder'):
   builder=resolve(s['packet_builder']); req(builder.is_file(),s['id']+' missing packet builder '+str(builder))
   py_compile.compile(str(builder),doraise=True)
  if s.get('stage_release_validator'):
   stage_validator=resolve(s['stage_release_validator']); req(stage_validator.is_file(),s['id']+' missing stage-release validator '+str(stage_validator))
   py_compile.compile(str(stage_validator),doraise=True)
  if s.get('entry_validator'):
   entry_validator=resolve(s['entry_validator']); req(entry_validator.is_file(),s['id']+' missing entry validator '+str(entry_validator))
   py_compile.compile(str(entry_validator),doraise=True)
  for t in s['templates']:
   p=resolve(t); req(p.is_file(),s['id']+' missing template '+str(p))
 p3=json.loads((ROOT/'templates/p3_stage_release.json').read_text()); req(p3['status']=='NOT_RUN','P3 release template must remain NOT_RUN')
 req(p3.get('release_scope')=='P3_COMPLETE_P4_ENTRY_ONLY','P3 release scope drift')
 req(p3.get('p4_energization_authorized') is False and p3.get('machine_release')=='HOLD','P3 release template must remain fail-closed')
 p4=json.loads((ROOT/'templates/p4_stage_release.json').read_text()); req(p4['status']=='NOT_RUN','P4 release template must remain NOT_RUN')
 req(p4.get('release_scope')=='P4_COMPLETE_REMAINING_CUTTER_REVIEW_ONLY','P4 release scope drift')
 req(p4.get('remaining_cut01_quantity')==10,'P4 remaining cutter count drift')
 req(p4.get('remaining_cut01_fabrication_authorized') is False and p4.get('downstream_energization_authorized') is False and p4.get('machine_release')=='HOLD','P4 release template must remain fail-closed')
 p5=json.loads((ROOT/'templates/p5_stage_release.json').read_text()); req(p5['status']=='NOT_RUN','P5 release template must remain NOT_RUN')
 req(p5.get('release_scope')=='P5_COUPON_COMPLETE_P6_REVIEW_ONLY','P5 release scope drift')
 req(p5.get('p6_entry_review') is False and p5.get('action_state')=='HOLD' and p5.get('machine_release')=='HOLD','P5 release template must remain fail-closed')
 p7=json.loads((ROOT/'templates/p7_stage_release.json').read_text()); req(p7['status']=='NOT_RUN','P7 release template must remain NOT_RUN')
 req(p7.get('release_scope')=='P7_LOGIC_SAFETY_COMPLETE_P8_P9_ENTRY_ONLY','P7 release scope drift')
 req(p7.get('motor_energization_authorized') is False and p7.get('heater_energization_authorized') is False and p7.get('machine_release')=='HOLD','P7 release template must remain fail-closed')
 text=(ROOT/'PHYSICAL_EXECUTION_INDEX_KO.md').read_text()
 for sid in expected: req(f'| {sid} |' in text,'index missing '+sid)
 print(f'PHYSICAL_EXECUTION_REGISTRY_OK stages={len(stages)} physical_authorized=false procurement_authorized=false')
if __name__=='__main__': main()
