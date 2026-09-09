# Practical make/reuse scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - practical_mvp  (2026-09-09)

## Corpus Check
- 6 files · ~336 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 49 nodes · 92 edges · 9 communities (2 shown, 7 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8

## God Nodes (most connected - your core abstractions)
1. `ResourceTests` - 14 edges
2. `PolicyTests` - 13 edges
3. `build()` - 10 edges
4. `route()` - 8 edges
5. `read_csv()` - 6 edges
6. `calculate()` - 6 edges
7. `target_material()` - 5 edges
8. `main()` - 5 edges
9. `sha()` - 4 edges
10. `main()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `read_csv()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `calculate()` --calls--> `target_material()`  [EXTRACTED]
  resource_budget.py → build_plan.py

## Import Cycles
- None detected.

## Communities (9 total, 7 thin omitted)

### Community 2 - "Community 2"
Cohesion: 0.53
Nodes (5): target_material(), calculate(), finite(), main(), Resource arithmetic on existing part manifests, not new slicer/PSU tests.

### Community 3 - "Community 3"
Cohesion: 0.60
Nodes (4): main(), User-asset and fabrication allocation; not donor performance qualification., sha(), write_csv()

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResourceTests` connect `Community 0` to `Community 5`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `PolicyTests` connect `Community 6` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._