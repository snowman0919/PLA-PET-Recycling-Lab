# Drive closeout review scoped graph

AST + reviewed source-located document links only. Not a full project or full visual-document semantic re-extraction. No paid API calls. Root project graph is preserved.

# Graph Report - drive_acceptance_v08  (2026-09-09)

## Corpus Check
- 8 files · ~810 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 36 nodes · 43 edges · 7 communities (5 shown, 2 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 1.0)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5

## God Nodes (most connected - your core abstractions)
1. `Tests` - 11 edges
2. `check_bindings()` - 4 edges
3. `main()` - 4 edges
4. `sha()` - 3 edges
5. `bound_path()` - 3 edges
6. `sha()` - 2 edges
7. `main()` - 2 edges
8. `sha()` - 2 edges
9. `main()` - 2 edges
10. `sha()` - 2 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (7 total, 2 thin omitted)

### Community 2 - "Community 2"
Cohesion: 0.67
Nodes (5): bound_path(), check_bindings(), main(), Validate a coherent drive-review snapshot, not physical commissioning., sha()

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (3): main(), Read the exported assembly and independently inspect functional bearing lands., sha()

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (3): main(), Compare actual drive setpoints to conditional demand, without raising limits., sha()

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): main(), Drive-only object register from the exported native assembly, not purchase…, sha()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Not enough signal to generate questions. This usually means the corpus has no AMBIGUOUS edges, no bridge nodes, no INFERRED relationships, and all communities are tightly cohesive. Add more files or run with --mode deep to extract richer edges._