"""Rebuild physical-v0.8 scoped graph using AST + literal reviewed anchors only."""
from pathlib import Path
import csv,hashlib,json,re
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster,score_all
from graphify.analyze import god_nodes,surprising_connections,suggest_questions
from graphify.report import generate
from graphify.export import to_json
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'graphify-out'

def main():
    OUT.mkdir(exist_ok=True)
    code=sorted(p for p in ROOT.glob('*.py') if p.name!='update_scoped_graph.py')+[ROOT/'update_scoped_graph.py']
    data=extract(code,cache_root=ROOT,root=ROOT,parallel=False)
    docs=sorted(ROOT.glob('*.md'))
    structured=sorted(ROOT.glob('*.json'))+sorted(ROOT.glob('*.csv'))+sorted((ROOT/'templates').glob('*.csv'))
    source_nodes={}
    for p in docs+structured:
        rel=str(p.relative_to(ROOT)); nid='document:'+rel
        data['nodes'].append({'id':nid,'label':p.name,'type':'document','source_file':rel}); source_nodes[rel]=nid
    code_nodes=[n for n in data['nodes'] if n.get('source_file')]
    all_files=code+docs+structured
    for p in docs+structured:
        rel=str(p.relative_to(ROOT)); nid=source_nodes[rel]
        try: text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        for target in all_files:
            if target==p: continue
            name=target.name
            if name not in text: continue
            target_rel=str(target.relative_to(ROOT))
            if target_rel in source_nodes: tid=source_nodes[target_rel]
            else:
                matches=[n for n in code_nodes if str(n.get('source_file','')).endswith(name)]
                if not matches: continue
                tid=matches[0]['id']
            data['edges'].append({'source':nid,'target':tid,'relation':'references','confidence':1.0,'evidence':'EXTRACTED','source_file':rel})
    # Explicit stage anchors from controlling contract: literal extraction, not inferred semantics.
    contract=ROOT/'physical_gate_contract.json'
    if contract.exists():
        c=json.loads(contract.read_text())
        cn=source_nodes.get('physical_gate_contract.json')
        stages=c.get('gates',[])
        stage_ids={g['id']:'stage:'+g['id'] for g in stages}
        for g in stages:
            gid=stage_ids[g['id']]; data['nodes'].append({'id':gid,'label':g['id']+' '+g['name'],'type':'stage','source_file':'physical_gate_contract.json'})
            data['edges'].append({'source':cn,'target':gid,'relation':'defines','confidence':1.0,'evidence':'EXTRACTED','source_file':'physical_gate_contract.json'})
        for g in stages:
            gid=stage_ids[g['id']]
            for field,relation in (('prerequisites','requires_stage'),('unlocks','unlocks_stage')):
                for line in g.get(field,[]):
                    for pid in re.findall(r'\bP(?:1[0-2]|[0-9])\b',line):
                        if pid in stage_ids and stage_ids[pid]!=gid:
                            data['edges'].append({'source':gid,'target':stage_ids[pid],'relation':relation,'confidence':1.0,'evidence':'EXTRACTED','source_file':'physical_gate_contract.json'})
    graph=build_from_json(data,root=str(ROOT),directed=True)
    communities=cluster(graph); cohesion=score_all(graph,communities); labels={k:'Community '+str(k) for k in communities}
    gods=god_nodes(graph); surprises=surprising_connections(graph,communities); questions=suggest_questions(graph,communities,labels)
    to_json(graph,communities,str(OUT/'graph.json'),force=True)
    detection={'total_files':len(all_files),'total_words':sum(len(p.read_text(encoding='utf-8',errors='ignore').split()) for p in docs+structured),'files':{'code':[str(p) for p in code],'document':[str(p) for p in docs+structured]}}
    report=generate(graph,communities,cohesion,labels,gods,surprises,detection,{'input':0,'output':0},str(ROOT),suggested_questions=questions)
    scope='# Physical v0.8 scoped graph\n\nAST + host-reviewed literal file/stage anchors only. No paid API calls. This is not a full semantic extraction of the repository.\n\n'
    (OUT/'GRAPH_REPORT.md').write_text(scope+report)
    (OUT/'manifest.json').write_text(json.dumps({'scope':'validation/physical_v08','method':'graphify AST + literal document/file/stage anchors','nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files}},ensure_ascii=False,indent=2)+'\n')
    (OUT/'cost.json').write_text(json.dumps({'additional_paid_api_calls':0,'additional_cost_usd':0,'tokens_measured':False,'scope':'local scoped graph only'},indent=2)+'\n')
    print(json.dumps({'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'communities':len(communities),'scope':str(ROOT)}))
if __name__=='__main__': main()
