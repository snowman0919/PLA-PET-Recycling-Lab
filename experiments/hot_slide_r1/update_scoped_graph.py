"""Rebuild this experiment's local graph with AST and reviewed document links."""
from pathlib import Path
import hashlib, json
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'graphify-out'

def main():
    OUT.mkdir(exist_ok=True)
    paths = sorted(ROOT.glob('*.py'))
    data = extract(paths, cache_root=ROOT, root=ROOT, parallel=False)
    docs = sorted(ROOT.glob('*.md'))
    ids = {n['id'] for n in data['nodes']}
    for p in docs:
        label = 'document:' + p.name
        data['nodes'].append({'id': label, 'label': p.name, 'type': 'document', 'source_file': p.name})
        for number, line in enumerate(p.read_text().splitlines(), 1):
            for target in paths:
                if target.name not in line:
                    continue
                matches = [n for n in data['nodes'] if n['id'] in ids and str(n.get('source_file', '')).endswith(target.name)]
                if matches:
                    data['edges'].append({'source': label, 'target': matches[0]['id'], 'relation': 'references', 'confidence': 1.0, 'evidence': 'EXTRACTED', 'source_file': p.name, 'source_location': str(number)})
    claims = [('README_KO.md', '실제 압출기 지지부 교체품이 아니다', 'fixture-not-machine-replacement'), ('README_KO.md', '실제 물리 시험 수는0', 'physical-tests-not-run'), ('TEST_INTENT.md', '두께방향 단독 최대응력은 수렴 완료가 아니다', 'face-gradient-not-converged')]
    for name, phrase, concept in claims:
        lines = (ROOT / name).read_text().splitlines()
        hit = next((i for i, line in enumerate(lines, 1) if phrase in line), None)
        if hit is None:
            raise ValueError('Reviewed semantic anchor changed: ' + concept)
        nid = 'contract:' + concept
        data['nodes'].append({'id': nid, 'label': concept, 'type': 'concept', 'source_file': name})
        data['edges'].append({'source': 'document:' + name, 'target': nid, 'relation': 'states', 'confidence': 1.0, 'evidence': 'EXTRACTED', 'source_file': name, 'source_location': str(hit)})
    graph = build_from_json(data, root=str(ROOT), directed=True)
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = {k: 'Community ' + str(k) for k in communities}
    gods = god_nodes(graph); surprises = surprising_connections(graph, communities)
    questions = suggest_questions(graph, communities, labels)
    to_json(graph, communities, str(OUT / 'graph.json'), force=True)
    detection = {'total_files': len(paths) + len(docs), 'total_words': sum(len(p.read_text().split()) for p in docs), 'files': {'code': [str(p) for p in paths], 'document': [str(p) for p in docs]}}
    report = generate(graph, communities, cohesion, labels, gods, surprises, detection, {'input': 0, 'output': 0}, str(ROOT), suggested_questions=questions)
    scope = '# HS-R1-S2 scoped graph\n\nAST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.\n\n'
    (OUT / 'GRAPH_REPORT.md').write_text(scope + report)
    (OUT / 'manifest.json').write_text(json.dumps({'scope': 'experiments/hot_slide_r1', 'method': 'graphify AST plus host-reviewed literal semantic anchors', 'nodes': graph.number_of_nodes(), 'edges': graph.number_of_edges(), 'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths + docs}}, indent=2))
    (OUT / 'cost.json').write_text(json.dumps({'additional_paid_api_calls': 0, 'additional_cost_usd': 0, 'tokens_measured': False, 'scope': 'local scoped graph only'}, indent=2))
    print(json.dumps({'nodes': graph.number_of_nodes(), 'edges': graph.number_of_edges(), 'communities': len(communities), 'scope': str(ROOT)}))

if __name__ == '__main__':
    main()
