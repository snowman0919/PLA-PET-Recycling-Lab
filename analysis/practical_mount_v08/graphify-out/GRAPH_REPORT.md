# Practical mount scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - practical_mount_v08  (2026-09-09)

## Corpus Check
- 6 files · ~664 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 30 nodes · 49 edges · 6 communities (3 shown, 3 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4

## God Nodes (most connected - your core abstractions)
1. `PracticalAuditTests` - 11 edges
2. `gap()` - 8 edges
3. `thrust()` - 7 edges
4. `growth()` - 6 edges
5. `main()` - 5 edges
6. `positive()` - 4 edges
7. `sha()` - 2 edges
8. `sha()` - 2 edges
9. `main()` - 2 edges
10. `Geometry-specific movement and pressure audit; not a pressure/fit approval.` - 1 edges

## Surprising Connections (you probably didn't know these)
- `thrust()` --calls--> `positive()`  [EXTRACTED]
  calculate.py → calculate.py  _Bridges community 3 → community 0_
- `gap()` --calls--> `positive()`  [EXTRACTED]
  calculate.py → calculate.py  _Bridges community 1 → community 0_

## Import Cycles
- None detected.

## Communities (6 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.36
Nodes (5): growth(), main(), positive(), Geometry-specific movement and pressure audit; not a pressure/fit approval., sha()

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (3): main(), Read-only FreeCAD station audit; no manufacturing geometry changes., sha()

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PracticalAuditTests` connect `Community 1` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `gap()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `thrust()` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._