# Practical make/reuse scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - practical_mvp  (2026-09-09)

## Corpus Check
- 11 files · ~699 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 70 nodes · 123 edges · 7 communities (4 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5

## God Nodes (most connected - your core abstractions)
1. `ResourceTests` - 14 edges
2. `PolicyTests` - 13 edges
3. `build()` - 10 edges
4. `validate()` - 10 edges
5. `SourceTests` - 9 edges
6. `route()` - 8 edges
7. `read_csv()` - 6 edges
8. `calculate()` - 6 edges
9. `target_material()` - 5 edges
10. `main()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `calculate()` --calls--> `target_material()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `main()` --calls--> `read_csv()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  resource_budget.py → build_plan.py

## Import Cycles
- None detected.

## Communities (7 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (11): main(), User-asset and fabrication allocation; not donor performance qualification., read_csv(), sha(), target_material(), write_csv(), calculate(), finite() (+3 more)

### Community 1 - "Community 1"
Cohesion: 0.19
Nodes (4): build(), route(), PolicyTests, Sourcing-policy regressions, not structural or physical qualification.

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (6): main(), Validate reviewed source records; no checkout or orders., read(), validate(), Cost records cannot invent inventory or a completed checkout., SourceTests

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResourceTests` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._