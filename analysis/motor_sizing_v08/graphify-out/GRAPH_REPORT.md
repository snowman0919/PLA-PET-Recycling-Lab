# Motor sizing scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - motor_sizing_v08  (2026-09-09)

## Corpus Check
- 9 files · ~874 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 65 nodes · 100 edges · 7 communities (3 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6

## God Nodes (most connected - your core abstractions)
1. `SelectionTests` - 17 edges
2. `SizingTests` - 17 edges
3. `validate()` - 9 edges
4. `scenarios()` - 8 edges
5. `independent()` - 7 edges
6. `run_case()` - 5 edges
7. `output()` - 5 edges
8. `main()` - 4 edges
9. `conservative_catalog_nm()` - 4 edges
10. `main()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `validate()` --calls--> `sha()`  [EXTRACTED]
  verify_study.py → verify_study.py  _Bridges community 4 → community 5_

## Import Cycles
- None detected.

## Communities (7 total, 4 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.25
Nodes (8): independent(), main(), mean(), Run bounded process-demand studies with a real OpenModelica executable., run_case(), scenarios(), sha(), Focused arithmetic and trace regressions; never a physical qualification.

### Community 2 - "Community 2"
Cohesion: 0.26
Nodes (7): Rebuild only this study with its recorded OpenModelica toolchain., conservative_catalog_nm(), main(), output(), Bind conditional demand to exact catalogue variants and complete option prices., sha(), Catalogue selection checks, not hardware approval.

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): main(), Numerical qualification of declared demand models, not physical motor tests., sha()

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SizingTests` connect `Community 3` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `validate()` connect `Community 4` to `Community 5`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._