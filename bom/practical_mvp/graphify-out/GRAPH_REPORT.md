# Practical make/reuse scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - practical_mvp  (2026-09-09)

## Corpus Check
- 4 files · ~371 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 27 nodes · 42 edges · 5 communities (1 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4

## God Nodes (most connected - your core abstractions)
1. `PolicyTests` - 13 edges
2. `build()` - 9 edges
3. `route()` - 7 edges
4. `main()` - 5 edges
5. `sha()` - 2 edges
6. `read_csv()` - 2 edges
7. `write_csv()` - 2 edges
8. `Build a proposal from observed BOMs; never certify donor parts or new CAD.` - 1 edges
9. `Sourcing-policy regressions, not structural or physical qualification.` - 1 edges
10. `Rebuild this experiment's local graph with AST and reviewed document links.` - 1 edges

## Surprising Connections (you probably didn't know these)
- `build()` --calls--> `route()`  [EXTRACTED]
  build_plan.py → build_plan.py  _Bridges community 0 → community 2_
- `main()` --calls--> `build()`  [EXTRACTED]
  build_plan.py → build_plan.py  _Bridges community 1 → community 0_

## Import Cycles
- None detected.

## Communities (5 total, 4 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.53
Nodes (5): main(), Build a proposal from observed BOMs; never certify donor parts or new CAD., read_csv(), sha(), write_csv()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PolicyTests` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `build()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._