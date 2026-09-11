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
 req(policy.get('mvp_is_final_product') is True,'MVP must remain the final product')
 req(policy.get('throwaway_prototype_allowed') is False,'throwaway prototype must remain prohibited')
 req(policy.get('design_feedback_required_on_smoke_failure') is True,'smoke failure must feed back into design')
 smoke=reg.get('smoke_contract',{})
 req(smoke.get('checkpoints')==[f'S{i}' for i in range(6)],'smoke checkpoint registry drift')
 for key in ('contract','doc'):
  req(resolve(smoke.get(key,'')).is_file(),'missing smoke '+key)
 smoke_contract=contract.get('mvp_final_identity',{})
 req(smoke_contract.get('mvp_is_final_product') is True and smoke_contract.get('same_physical_artifact_required') is True,'gate MVP identity drift')
 req(smoke_contract.get('throwaway_prototype_allowed') is False and smoke_contract.get('failure_policy')=='HOLD_AND_REVISE','gate smoke failure policy drift')
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
  if s.get('firmware_profile_builder'):
   profile_builder=resolve(s['firmware_profile_builder']); req(profile_builder.is_file(),s['id']+' missing firmware profile builder '+str(profile_builder))
   py_compile.compile(str(profile_builder),doraise=True)
  if s.get('stage_release_validator'):
   stage_validator=resolve(s['stage_release_validator']); req(stage_validator.is_file(),s['id']+' missing stage-release validator '+str(stage_validator))
   py_compile.compile(str(stage_validator),doraise=True)
  if s.get('firmware_commissioning_validator'):
   fw_validator=resolve(s['firmware_commissioning_validator']); req(fw_validator.is_file(),s['id']+' missing firmware commissioning validator '+str(fw_validator))
   py_compile.compile(str(fw_validator),doraise=True)
  if s.get('entry_validator'):
   entry_validator=resolve(s['entry_validator']); req(entry_validator.is_file(),s['id']+' missing entry validator '+str(entry_validator))
   py_compile.compile(str(entry_validator),doraise=True)
  for key in ('p3_entry_validator','p5_entry_validator'):
   if s.get(key):
    entry_validator=resolve(s[key]); req(entry_validator.is_file(),s['id']+' missing '+key+' '+str(entry_validator))
    py_compile.compile(str(entry_validator),doraise=True)
  for t in s['templates']:
   p=resolve(t); req(p.is_file(),s['id']+' missing template '+str(p))
 p3=json.loads((ROOT/'templates/p3_stage_release.json').read_text()); req(p3['status']=='NOT_RUN','P3 release template must remain NOT_RUN')
 req(p3.get('release_scope')=='P3_COMPLETE_P4_P6_ENTRY_ONLY','P3 release scope drift')
 req(p3.get('p4_entry_review') is False and p3.get('p6_entry_review') is False and p3.get('p4_energization_authorized') is False and p3.get('p6_energization_authorized') is False and p3.get('machine_release')=='HOLD','P3 release template must remain fail-closed')
 p4=json.loads((ROOT/'templates/p4_stage_release.json').read_text()); req(p4['status']=='NOT_RUN','P4 release template must remain NOT_RUN')
 req(p4.get('release_scope')=='P4_COMPLETE_REMAINING_CUTTER_REVIEW_ONLY','P4 release scope drift')
 req(p4.get('remaining_cut01_quantity')==10,'P4 remaining cutter count drift')
 req(p4.get('remaining_cut01_fabrication_authorized') is False and p4.get('downstream_energization_authorized') is False and p4.get('machine_release')=='HOLD','P4 release template must remain fail-closed')
 p5=json.loads((ROOT/'templates/p5_stage_release.json').read_text()); req(p5['status']=='NOT_RUN','P5 release template must remain NOT_RUN')
 req(p5.get('release_scope')=='P5_COUPON_COMPLETE_P6_REVIEW_ONLY','P5 release scope drift')
 req(p5.get('p6_entry_review') is False and p5.get('action_state')=='HOLD' and p5.get('machine_release')=='HOLD','P5 release template must remain fail-closed')
 p6_stage=next(s for s in stages if s['id']=='P6')
 req(p6_stage.get('p3_entry_validator')=='validate_p3_stage_release.py' and p6_stage.get('p5_entry_validator')=='validate_p5_stage_release.py','P6 dual entry-validator drift')
 p6=json.loads((ROOT/'templates/p6_stage_release.json').read_text()); req(p6['status']=='NOT_RUN','P6 release template must remain NOT_RUN')
 req(p6.get('release_scope')=='P6_COLD_EXTRUDER_COMPLETE_P8_ENTRY_ONLY','P6 release scope drift')
 req(p6.get('p3_release') is None and p6.get('p3_release_sha256') is None,'P6 template must explicitly bind P3 release at execution time')
 req(p6.get('motor_energization_authorized') is False and p6.get('heater_energization_authorized') is False and p6.get('machine_release')=='HOLD','P6 release template must remain fail-closed')
 p7=json.loads((ROOT/'templates/p7_stage_release.json').read_text()); req(p7['status']=='NOT_RUN','P7 release template must remain NOT_RUN')
 req(p7.get('release_scope')=='P7_LOGIC_SAFETY_COMPLETE_P8_P9_ENTRY_ONLY','P7 release scope drift')
 req(p7.get('motor_energization_authorized') is False and p7.get('heater_energization_authorized') is False and p7.get('machine_release')=='HOLD','P7 release template must remain fail-closed')
 p8=json.loads((ROOT/'templates/p8_stage_release.json').read_text()); req(p8['status']=='NOT_RUN','P8 release template must remain NOT_RUN')
 req(p8.get('release_scope')=='P8_DRY_RUN_COMPLETE_P9_ENTRY_ONLY','P8 release scope drift')
 req(p8.get('heater_energization_authorized') is False and p8.get('machine_release')=='HOLD','P8 release template must remain fail-closed')
 text=(ROOT/'PHYSICAL_EXECUTION_INDEX_KO.md').read_text()
 for sid in expected: req(f'| {sid} |' in text,'index missing '+sid)
 print(f'PHYSICAL_EXECUTION_REGISTRY_OK stages={len(stages)} physical_authorized=false procurement_authorized=false')
if __name__=='__main__': main()
