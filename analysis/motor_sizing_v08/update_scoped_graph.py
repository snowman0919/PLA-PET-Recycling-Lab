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
        label = 'document:' + str(p.relative_to(ROOT))
        data['nodes'].append({'id': label, 'label': p.name, 'type': 'document', 'source_file': str(p.relative_to(ROOT))})
        for number, line in enumerate(p.read_text().splitlines(), 1):
            for target in paths:
                if target.name not in line:
                    continue
                matches = [n for n in data['nodes'] if n['id'] in ids and str(n.get('source_file', '')).endswith(target.name)]
                if matches:
                    data['edges'].append({'source': label, 'target': matches[0]['id'], 'relation': 'references', 'confidence': 1.0, 'evidence': 'EXTRACTED', 'source_file': str(p.relative_to(ROOT)), 'source_location': str(number)})
    graph = build_from_json(data, root=str(ROOT), directed=True)
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = {k: 'Community ' + str(k) for k in communities}
    gods = god_nodes(graph); surprises = surprising_connections(graph, communities)
    questions = suggest_questions(graph, communities, labels)
    to_json(graph, communities, str(OUT / 'graph.json'), force=True)
    detection = {'total_files': len(paths) + len(docs), 'total_words': sum(len(p.read_text().split()) for p in docs), 'files': {'code': [str(p) for p in paths], 'document': [str(p) for p in docs]}}
    report = generate(graph, communities, cohesion, labels, gods, surprises, detection, {'input': 0, 'output': 0}, str(ROOT), suggested_questions=questions)
    scope = '# Motor sizing scoped graph\n\nAST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.\n\n'
    (OUT / 'GRAPH_REPORT.md').write_text(scope + report)
    (OUT / 'manifest.json').write_text(json.dumps({'scope': 'analysis/motor_sizing_v08', 'method': 'graphify AST plus host-reviewed literal semantic anchors', 'nodes': graph.number_of_nodes(), 'edges': graph.number_of_edges(), 'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths + docs}}, indent=2))
    (OUT / 'cost.json').write_text(json.dumps({'additional_paid_api_calls': 0, 'additional_cost_usd': 0, 'tokens_measured': False, 'scope': 'local scoped graph only'}, indent=2))
    print(json.dumps({'nodes': graph.number_of_nodes(), 'edges': graph.number_of_edges(), 'communities': len(communities), 'scope': str(ROOT)}))

if __name__ == '__main__':
    main()
