#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def validate(path:Path=HERE/'mvp_smoke_contract.json') -> dict:
    d=json.loads(path.read_text(encoding='utf-8'))
    ident=d['identity']; auth=d['authorization']; loop=d['feedback_loop']
    if ident.get('mvp_is_final_product') is not True or ident.get('same_physical_artifact_required') is not True:
        raise ValueError('MVP/final product identity drift')
    if ident.get('throwaway_prototype_allowed') is not False:
        raise ValueError('throwaway prototype must remain prohibited')
    if any(value is not False for value in auth.values()):
        raise ValueError('smoke contract must not authorize physical action')
    cps=d['checkpoints']; ids=[x['id'] for x in cps]
    if ids != [f'S{i}' for i in range(6)]: raise ValueError('smoke checkpoint order drift')
    valid_p={f'P{i}' for i in range(13)}
    if any(not set(x['before_or_with']) <= valid_p for x in cps): raise ValueError('invalid P-stage binding')
    if loop.get('on_any_failure')!='HOLD_AND_REVISE' or loop.get('acceptance_relaxation_allowed') is not False or loop.get('field_rework_without_design_record_allowed') is not False:
        raise ValueError('feedback loop must remain fail-closed')
    required={'preserve raw evidence and exact hardware configuration','regenerate affected release artifacts and rerun digital validators','invalidate downstream physical stage releases whose source bindings changed','repeat the failed smoke checkpoint before proceeding'}
    if not required <= set(loop.get('steps',[])): raise ValueError('feedback loop incomplete')
    return {'status':'MVP_SMOKE_CONTRACT_PASS','mvp_is_final_product':True,'checkpoints':len(cps),'physical_action_authorized':False,'machine_release':'HOLD'}

def main():
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
