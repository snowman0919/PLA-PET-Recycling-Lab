"""Rebuild physical-v0.8 scoped graph using AST + literal reviewed anchors only."""
from pathlib import Path
import hashlib,json,re
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster,score_all
from graphify.analyze import god_nodes,surprising_connections,suggest_questions
from graphify.report import generate
from graphify.export import to_json
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
OUT=ROOT/'graphify-out'
GENERATED={'simulation_prerequisite.json','stage_status.json'}
EXTERNAL=[
    PROJECT/'cad/generation/generate_manufacturing.py',
    PROJECT/'exports/cnc/extruder/inspection_report_template.csv',
    PROJECT/'docs/final/specialist_hot_zone_inquiry_email_en.txt',
    PROJECT/'docs/final/specialist_hot_zone_supplier_response.csv',
]
def rel(p): return str(p.relative_to(PROJECT))

def main():
    OUT.mkdir(exist_ok=True)
    local_code=sorted(p for p in ROOT.glob('*.py') if p.name!='update_scoped_graph.py')+[ROOT/'update_scoped_graph.py']
    code=local_code+[p for p in EXTERNAL if p.suffix=='.py' and p.is_file()]
    data=extract(code,cache_root=ROOT,root=PROJECT,parallel=False)
    docs=sorted(ROOT.glob('*.md'))+[p for p in EXTERNAL if p.suffix in {'.md','.txt'} and p.is_file()]
    structured=[p for p in sorted(ROOT.glob('*.json')) if p.name not in GENERATED]
    structured+=sorted(ROOT.glob('*.csv'))+sorted((ROOT/'templates').glob('*.csv'))
    structured+=[p for p in EXTERNAL if p.suffix in {'.json','.csv'} and p.is_file()]
    # Preserve order while removing duplicates.
    docs=list(dict.fromkeys(docs)); structured=list(dict.fromkeys(structured)); code=list(dict.fromkeys(code))
    source_nodes={}
    for p in docs+structured:
        rp=rel(p); nid='document:'+rp
        data['nodes'].append({'id':nid,'label':p.name,'type':'document','source_file':rp}); source_nodes[rp]=nid
    code_nodes=[n for n in data['nodes'] if n.get('source_file')]
    all_files=code+docs+structured
    for p in docs+structured:
        rp=rel(p); nid=source_nodes[rp]
        text=p.read_text(encoding='utf-8',errors='ignore')
        for target in all_files:
            if target==p: continue
            name=target.name
            if name not in text: continue
            target_rel=rel(target)
            if target_rel in source_nodes: tid=source_nodes[target_rel]
            else:
                matches=[n for n in code_nodes if str(n.get('source_file','')).endswith(target_rel) or str(n.get('source_file','')).endswith(name)]
                if not matches: continue
                tid=matches[0]['id']
            data['edges'].append({'source':nid,'target':tid,'relation':'references','confidence':1.0,'evidence':'EXTRACTED','source_file':rp})
    contract=ROOT/'physical_gate_contract.json'
    if contract.exists():
        c=json.loads(contract.read_text()); cn=source_nodes.get(rel(contract)); stages=c.get('gates',[])
        stage_ids={g['id']:'stage:'+g['id'] for g in stages}
        for g in stages:
            gid=stage_ids[g['id']]; data['nodes'].append({'id':gid,'label':g['id']+' '+g['name'],'type':'stage','source_file':rel(contract)})
            data['edges'].append({'source':cn,'target':gid,'relation':'defines','confidence':1.0,'evidence':'EXTRACTED','source_file':rel(contract)})
        for g in stages:
            gid=stage_ids[g['id']]
            for field,relation in (('prerequisites','requires_stage'),('unlocks','unlocks_stage')):
                for line in g.get(field,[]):
                    for pid in re.findall(r'\bP(?:1[0-2]|[0-9])\b',line):
                        if pid in stage_ids and stage_ids[pid]!=gid:
                            data['edges'].append({'source':gid,'target':stage_ids[pid],'relation':relation,'confidence':1.0,'evidence':'EXTRACTED','source_file':rel(contract)})
    graph=build_from_json(data,root=str(PROJECT),directed=True)
    communities=cluster(graph); cohesion=score_all(graph,communities); labels={k:'Community '+str(k) for k in communities}
    gods=god_nodes(graph); surprises=surprising_connections(graph,communities); questions=suggest_questions(graph,communities,labels)
    to_json(graph,communities,str(OUT/'graph.json'),force=True)
    detection={'total_files':len(all_files),'total_words':sum(len(p.read_text(encoding='utf-8',errors='ignore').split()) for p in docs+structured),'files':{'code':[str(p) for p in code],'document':[str(p) for p in docs+structured]}}
    report=generate(graph,communities,cohesion,labels,gods,surprises,detection,{'input':0,'output':0},str(ROOT),suggested_questions=questions)
    scope='# Physical v0.8 scoped graph\n\nAST + host-reviewed literal file/stage anchors for `validation/physical_v08` plus explicitly bound P5 RFQ generator/inspection/inquiry sources. No paid API calls. This is not a full repository semantic extraction.\n\n'
    (OUT/'GRAPH_REPORT.md').write_text(scope+report)
    manifest={'scope':'validation/physical_v08 + selected P5 external bindings','method':'graphify AST + literal document/file/stage anchors','nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'source_sha256':{rel(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (OUT/'cost.json').write_text(json.dumps({'additional_paid_api_calls':0,'additional_cost_usd':0,'tokens_measured':False,'scope':'local scoped graph only'},indent=2)+'\n')
    print(json.dumps({'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'communities':len(communities),'sources':len(all_files),'scope':manifest['scope']}))
if __name__=='__main__': main()
