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
  for t in s['templates']:
   p=resolve(t); req(p.is_file(),s['id']+' missing template '+str(p))
 p3=json.loads((ROOT/'templates/p3_stage_release.json').read_text()); req(p3['status']=='NOT_RUN','P3 release template must remain NOT_RUN')
 text=(ROOT/'PHYSICAL_EXECUTION_INDEX_KO.md').read_text()
 for sid in expected: req(f'| {sid} |' in text,'index missing '+sid)
 print(f'PHYSICAL_EXECUTION_REGISTRY_OK stages={len(stages)} physical_authorized=false procurement_authorized=false')
if __name__=='__main__': main()
