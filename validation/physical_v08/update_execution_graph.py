"""Build a no-paid-API graph for the physical execution contracts only."""
from pathlib import Path
import hashlib,json
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster,score_all
from graphify.analyze import god_nodes,surprising_connections,suggest_questions
from graphify.report import generate
from graphify.export import to_json
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
OUT=ROOT/'graphify-execution-out'

def rel(p): return str(p.relative_to(PROJECT))
def main():
 OUT.mkdir(exist_ok=True)
 code=sorted(p for p in ROOT.glob('analyze_*.py'))+[ROOT/'simulation_prerequisite.py',ROOT/'validate_execution_registry.py',ROOT/'build_physical_launch_package.py',ROOT/'validate_physical_launch_package.py',ROOT/'update_execution_graph.py',ROOT/'p1_semantics.py',ROOT/'profile_nesting.py',ROOT/'frame_release.py']
 code += [PROJECT/rel for rel in (
  'cad/freecad/compact/geometry.py','cad/freecad/compact/traverse_revision.py',
  'cad/freecad/compact/shaft_retention.py','validation/shaft_retention_clearance.py',
  'release/build_mechanical_release.py','validation/test_native_model_handoff.py',
  'validation/test_shaft_retention_geometry.py',
  'cad/freecad/drive_v08/assembly.py','cad/freecad/drive_v08/frame_revision.py',
  'validation/integrated_assembly_clearance.py','validation/integrated_motion_clearance.py',
  'analysis/frame_v08/audit_geometry.py','analysis/frame_v08/beam_screen.py',
  'analysis/frame_v08/compare_published.py','release/build_frame_release.py')]
 code=[p for p in dict.fromkeys(code) if p.is_file()]
 docs=sorted(ROOT.glob('P*_KO.md'))+[ROOT/'PHYSICAL_BUILD_READINESS_KO.md',ROOT/'PHYSICAL_EXECUTION_INDEX_KO.md',ROOT/'FRAME_R1_EXECUTION_KO.md']
 docs += [PROJECT/'docs/reviews/geometry-closure-v08/README_KO.md', PROJECT/'docs/reviews/geometry-closure-v08/TRAVERSE_RETENTION_KO.md']
 docs=[p for p in dict.fromkeys(docs) if p.is_file()]
 structured=[ROOT/'physical_gate_contract.json',ROOT/'physical_execution_registry.json',ROOT/'stage_minimum_bom.csv',ROOT/'fabrication_sequence.csv',ROOT/'inventory_confirmation.csv',ROOT/'measurement_equipment.csv']
 structured+=[p for p in sorted((ROOT/'templates').iterdir()) if p.is_file()]
 structured += [PROJECT/'docs/reviews/geometry-closure-v08/retention_verification.json']
 structured=[p for p in dict.fromkeys(structured) if p.is_file()]
 data=extract(code,cache_root=ROOT,root=PROJECT,parallel=False)
 source_nodes={}
 for p in docs+structured:
  rp=rel(p); nid='document:'+rp; data['nodes'].append({'id':nid,'label':p.name,'type':'document','source_file':rp}); source_nodes[p.name]=nid
 for p in docs+structured:
  text=p.read_text(encoding='utf-8',errors='ignore'); src='document:'+rel(p)
  for name,nid in source_nodes.items():
   if name!=p.name and name in text: data['edges'].append({'source':src,'target':nid,'relation':'references','confidence':1.0,'evidence':'EXTRACTED','source_file':rel(p)})
 contract=json.loads((ROOT/'physical_gate_contract.json').read_text()); reg=json.loads((ROOT/'physical_execution_registry.json').read_text())
 for stage in contract['gates']:
  sid='stage:'+stage['id']; data['nodes'].append({'id':sid,'label':stage['id']+' '+stage['name'],'type':'stage','source_file':rel(ROOT/'physical_gate_contract.json')})
  data['edges'].append({'source':'document:'+rel(ROOT/'physical_gate_contract.json'),'target':sid,'relation':'defines','confidence':1.0,'evidence':'EXTRACTED','source_file':rel(ROOT/'physical_gate_contract.json')})
 for stage in reg['stages']:
  sid='stage:'+stage['id']; data['edges'].append({'source':'document:'+rel(ROOT/'physical_execution_registry.json'),'target':sid,'relation':'registers','confidence':1.0,'evidence':'EXTRACTED','source_file':rel(ROOT/'physical_execution_registry.json')})
 graph=build_from_json(data,root=str(PROJECT),directed=True); communities=cluster(graph); cohesion=score_all(graph,communities); labels={k:'Community '+str(k) for k in communities}
 to_json(graph,communities,str(OUT/'graph.json'),force=True)
 files=code+docs+structured; detection={'total_files':len(files),'total_words':sum(len(p.read_text(encoding='utf-8',errors='ignore').split()) for p in docs+structured),'files':{'code':[str(p) for p in code],'document':[str(p) for p in docs+structured]}}
 report=generate(graph,communities,cohesion,labels,god_nodes(graph),surprising_connections(graph,communities),detection,{'input':0,'output':0},str(ROOT),suggested_questions=suggest_questions(graph,communities,labels))
 (OUT/'GRAPH_REPORT.md').write_text('# Physical execution scoped graph\n\nP0-P12 execution contracts plus scoped integrated geometry and R1 dependencies. AST + literal reviewed anchors; no paid API calls; not a full-repository semantic graph.\n\n'+report)
 (OUT/'manifest.json').write_text(json.dumps({'scope':'P0-P12 and integrated geometry R1/R2 dependency review','method':'graphify AST + literal reviewed anchors','nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'source_sha256':{rel(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},ensure_ascii=False,indent=2)+'\n')
 (OUT/'cost.json').write_text(json.dumps({'additional_paid_api_calls':0,'additional_cost_usd':0,'scope':'local execution graph only'},indent=2)+'\n')
 print(json.dumps({'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'sources':len(files),'communities':len(communities)}))
if __name__=='__main__': main()
