# Practical make/reuse scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - practical_mvp  (2026-09-09)

## Corpus Check
- 15 files · ~1,058 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 102 nodes · 180 edges · 10 communities (6 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.97)
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
1. `Tests` - 19 edges
2. `ResourceTests` - 14 edges
3. `PolicyTests` - 13 edges
4. `operating_point()` - 12 edges
5. `build()` - 10 edges
6. `validate()` - 10 edges
7. `SourceTests` - 9 edges
8. `envelope()` - 9 edges
9. `route()` - 8 edges
10. `read_csv()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `calculate()` --calls--> `target_material()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `main()` --calls--> `read_csv()`  [EXTRACTED]
  resource_budget.py → build_plan.py
- `main()` --calls--> `sha()`  [EXTRACTED]
  resource_budget.py → build_plan.py

## Import Cycles
- None detected.

## Communities (10 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (11): main(), User-asset and fabrication allocation; not donor performance qualification., read_csv(), sha(), target_material(), write_csv(), calculate(), finite() (+3 more)

### Community 1 - "Community 1"
Cohesion: 0.19
Nodes (4): build(), route(), PolicyTests, Sourcing-policy regressions, not structural or physical qualification.

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (6): main(), Validate reviewed source records; no checkout or orders., read(), validate(), Cost records cannot invent inventory or a completed checkout., SourceTests

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (4): Software checks of units and rated-point comparison, not motor tests., apply_reply(), main(), Overlay user-reported inventory, without approving electrical compatibility.

### Community 6 - "Community 6"
Cohesion: 0.28
Nodes (4): envelope(), main(), positive(), Check published rated operating points; not physical motor acceptance.

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Tests` connect `Community 3` to `Community 5`, `Community 6`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `ResourceTests` connect `Community 4` to `Community 0`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._