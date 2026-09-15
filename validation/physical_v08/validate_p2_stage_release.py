#!/usr/bin/env python3
"""Revalidate reviewed P2 cold-fit evidence before P3/P5 entry review."""
from __future__ import annotations
import argparse, datetime, hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ANALYZER=ROOT/'validation/physical_v08/analyze_p2_records.py'


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def load_analyzer():
    spec=importlib.util.spec_from_file_location('ppr_p2_release_analyzer',ANALYZER)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load P2 analyzer')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def repo_file(value,release_path:Path,label:str)->Path:
    if value is None or not str(value).strip(): raise ValueError(label+' missing')
    p=Path(value); p=p if p.is_absolute() else release_path.parent/p; p=p.resolve()
    if not p.is_relative_to(ROOT) or not p.is_file(): raise ValueError(label+' must resolve to repository file')
    return p

def require_time(value):
    if not isinstance(value,str) or not value.strip(): raise ValueError('P2 release missing reviewed_at')
    parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None: raise ValueError('reviewed_at must include timezone')


def validate(path:Path,analyzer=None)->dict:
    path=path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file(): raise ValueError('P2 stage release must be repository file')
    release=json.loads(path.read_text(encoding='utf-8'))
    if release.get('stage')!='P2' or release.get('status')!='PASS': raise ValueError('P2 physical release is not PASS')
    if release.get('release_scope')!='P2_COLD_FRAME_FIT_COMPLETE_P3_ENTRY_ONLY': raise ValueError('P2 release scope invalid')
    if release.get('motor_energization_authorized') is not False or release.get('further_fabrication_authorized') is not False:
        raise ValueError('P2 release authorization semantics invalid')
    if release.get('machine_release')!='HOLD': raise ValueError('P2 machine release must remain HOLD')
    for field in ('approved_by','independent_reviewer'):
        if not isinstance(release.get(field),str) or not release[field].strip(): raise ValueError('P2 release missing '+field)
    if release['approved_by'].strip()==release['independent_reviewer'].strip(): raise ValueError('P2 release requires independent reviewer')
    require_time(release.get('reviewed_at'))
    files={
        'p1_inventory_sha256':repo_file(release.get('p1_inventory'),path,'P1 inventory'),
        'ggm_packet_sha256':repo_file(release.get('ggm_packet'),path,'GGM packet'),
        'profile_stock_sha256':repo_file(release.get('profile_stock'),path,'profile stock'),
        'fabrication_approval_sha256':repo_file(release.get('fabrication_approval'),path,'P2 fabrication approval'),
        'p2_record_sha256':repo_file(release.get('p2_record'),path,'P2 record'),
        'p2_result_sha256':repo_file(release.get('p2_result'),path,'P2 result'),
    }
    for field,target in files.items():
        if release.get(field)!=sha(target): raise ValueError(field+' mismatch')
    kerf=float(release.get('kerf_budget_mm'))
    saved=json.loads(files['p2_result_sha256'].read_text(encoding='utf-8'))
    authority=analyzer or load_analyzer()
    args=(files['p2_record_sha256'],files['p1_inventory_sha256'],files['ggm_packet_sha256'],files['profile_stock_sha256'],kerf,files['fabrication_approval_sha256'])
    fresh=authority(*args) if analyzer is not None else authority.evaluate(*args)
    if saved.get('status')!='P2_RECORD_CHECK_PASS' or fresh.get('status')!='P2_RECORD_CHECK_PASS': raise ValueError('P2 analyzer result is not PASS')
    if saved.get('record_sha256')!=fresh.get('record_sha256') or fresh.get('record_sha256')!=sha(files['p2_record_sha256']): raise ValueError('P2 record binding drift')
    if saved.get('prerequisites')!=fresh.get('prerequisites'): raise ValueError('P2 prerequisite binding drift')
    if saved.get('source_bindings_sha256')!=fresh.get('source_bindings_sha256'): raise ValueError('P2 source binding drift')
    for field in ('fabrication_authorized','energization_authorized','stage_release_granted'):
        if saved.get(field) is not False or fresh.get(field) is not False: raise ValueError('P2 analyzer authorization semantics drift: '+field)
    return {
        'status':'P2_STAGE_RELEASE_VALIDATED','stage':'P2','p3_entry_prerequisite':True,'p5_entry_prerequisite':True,
        'motor_energization_authorized':False,'further_fabrication_authorized':False,'machine_release':'HOLD',
        **{field:sha(target) for field,target in files.items()},'kerf_budget_mm':kerf,
        'p2_analyzer_sha256':sha(ANALYZER),'approved_by':release['approved_by'],
        'independent_reviewer':release['independent_reviewer'],'reviewed_at':release['reviewed_at']}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('release',type=Path); ap.add_argument('--output',type=Path); args=ap.parse_args()
    try: result=validate(args.release); code=0
    except (ValueError,KeyError,TypeError,FileNotFoundError,json.JSONDecodeError) as exc:
        result={'status':'NOT_RUN_OR_REJECTED','p3_entry_prerequisite':False,'p5_entry_prerequisite':False,
                'motor_energization_authorized':False,'further_fabrication_authorized':False,'machine_release':'HOLD','reason':str(exc)}; code=2
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'; print(text,end='')
    if args.output: args.output.write_text(text,encoding='utf-8')
    raise SystemExit(code)

if __name__=='__main__': main()
