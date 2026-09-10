#!/usr/bin/env python3
"""Offline profile nesting check. Reads measurements only; never authorizes cutting."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CUTLIST=ROOT/'exports/fabrication/frame_cut_list.csv'

def requirements():
    out={}
    with CUTLIST.open(newline='', encoding='utf-8') as fh:
      source=list(csv.DictReader(fh))
    for r in source:
        typ='2020' if r['stock'].startswith('20x20') else '2040' if r['stock'].startswith('20x40') else None
        if typ:
            out.setdefault(typ,[]).extend([(r['part_id'],float(r['cut_length_mm']))]*int(r['quantity']))
    return out

def measured(path):
    out={'2020':[],'2040':[]}
    with path.open(newline='', encoding='utf-8') as fh:
      source=list(csv.DictReader(fh))
    for r in source:
        typ=r.get('profile_type','').strip().upper().replace('X','')
        typ={'2020':'2020','2040':'2040'}.get(typ)
        if not typ or r.get('status','').strip().upper() not in {'MEASURED','PASS','USABLE'}: continue
        out[typ].append((r['record_id'],float(r['usable_length_mm'])))
    return out

def solve(cuts,bars,kerf):
    cuts=sorted(cuts,key=lambda x:x[1],reverse=True); bars=sorted(bars,key=lambda x:x[1],reverse=True)
    rem=[b[1] for b in bars]; plan=[[] for _ in bars]
    def rec(i):
        if i==len(cuts): return True
        pid,L=cuts[i]; need=L+kerf; seen=set()
        for j,r in enumerate(rem):
            key=round(r,6)
            if key in seen or r+1e-9<need: continue
            seen.add(key); rem[j]-=need; plan[j].append((pid,L))
            if rec(i+1): return True
            plan[j].pop(); rem[j]+=need
        return False
    ok=rec(0)
    return ok,[{'stock_id':bars[i][0],'stock_mm':bars[i][1],'cuts':plan[i],'leftover_mm':round(rem[i],3)} for i in range(len(bars))]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('measurements',type=Path); ap.add_argument('--kerf-mm',type=float,required=True); ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.kerf_mm<0: raise SystemExit('kerf must be >=0')
    req=requirements(); stock=measured(a.measurements)
    result={'status':'PASS','cut_authorization':False,'kerf_mm':a.kerf_mm,'profiles':{}}
    for typ in ('2020','2040'):
        if not stock[typ]:
            result['profiles'][typ]={'status':'NOT_RUN','required_piece_count':len(req[typ])}; result['status']='NOT_RUN'; continue
        ok,plan=solve(req[typ],stock[typ],a.kerf_mm)
        result['profiles'][typ]={'status':'PASS' if ok else 'INSUFFICIENT_OR_UNNESTABLE','required_piece_count':len(req[typ]),'required_raw_mm':sum(x[1] for x in req[typ]),'measured_usable_mm':sum(x[1] for x in stock[typ]),'plan':plan if ok else []}
        if not ok: result['status']='FAIL'
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output: a.output.write_text(text)
    print(text,end='')
    raise SystemExit(0 if result['status'] in {'PASS','NOT_RUN'} else 2)
if __name__=='__main__': main()
