# Release finalization scoped graph

AST and document nodes only; no paid API calls. Not a full-repository semantic update.

# Graph Report - PPR  (2026-09-12)

## Corpus Check
- 16 files · ~2,083 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 90 nodes · 165 edges · 12 communities (9 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Release 0
- Release 1
- Release 2
- Release 3
- Release 4
- Release 5
- Release 6

## God Nodes (most connected - your core abstractions)
1. `main()` - 10 edges
2. `verify()` - 9 edges
3. `main()` - 9 edges
4. `export_metal_parts()` - 8 edges
5. `main()` - 8 edges
6. `safe_name()` - 7 edges
7. `normalize_zip_container()` - 7 edges
8. `export_print_part()` - 7 edges
9. `sha()` - 6 edges
10. `validate_contents()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `digest()`  [INFERRED]
  release/render_handoff.py → validation/ci_v08.py
- `main()` --calls--> `source_identity()`  [INFERRED]
  validation/ci_v08.py → release/source_identity.py
- `main()` --calls--> `export_metal_parts()`  [EXTRACTED]
  release/build_mechanical_release.py → cad/freecad/compact/generate.py
- `overview()` --calls--> `safe_name()`  [EXTRACTED]
  release/build_complete_release.py → release/verify_complete_release.py
- `main()` --calls--> `validate_policy()`  [EXTRACTED]
  release/build_complete_release.py → release/publication_policy.py

## Import Cycles
- None detected.

## Communities (12 total, 3 thin omitted)

### Community 0 - "Release 0"
Cohesion: 0.20
Nodes (21): dirs(), export_assembly(), export_metal_parts(), export_plates(), export_print_part(), export_review_keepouts(), export_tolerance_coupon(), feature() (+13 more)

### Community 1 - "Release 1"
Cohesion: 0.24
Nodes (17): git(), info(), json_bytes(), main(), overview(), publication_policy_current(), Path, Publishing a design prerelease never authorizes physical operation. (+9 more)

### Community 2 - "Release 2"
Cohesion: 0.25
Nodes (18): compile_pdf(), copy_part(), datum_for(), drawing_svg(), family(), hot_zone_parts(), inspection_for(), main() (+10 more)

### Community 3 - "Release 3"
Cohesion: 0.27
Nodes (8): main(), Path, Resolve local Git identity or export metadata; external package verification…, source_identity(), digest(), execute(), main(), Path

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Not enough signal to generate questions. This usually means the corpus has no AMBIGUOUS edges, no bridge nodes, no INFERRED relationships, and all communities are tightly cohesive. Add more files or run with --mode deep to extract richer edges._