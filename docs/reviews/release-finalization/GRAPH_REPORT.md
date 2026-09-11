# Release finalization scoped graph

AST and literal document anchors only; no paid API calls. Not a full-repository semantic update.

# Graph Report - PPR  (2026-09-12)

## Corpus Check
- 13 files · ~2,083 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 47 nodes · 76 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Release 0
- Release 1
- Release 2
- Release 3
- Release 4
- Release 5

## God Nodes (most connected - your core abstractions)
1. `main()` - 10 edges
2. `verify()` - 9 edges
3. `safe_name()` - 7 edges
4. `sha()` - 6 edges
5. `validate_contents()` - 6 edges
6. `CompletePackageTest` - 6 edges
7. `main()` - 4 edges
8. `validate_policy()` - 4 edges
9. `digest()` - 4 edges
10. `execute()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `digest()`  [INFERRED]
  release/render_handoff.py → validation/ci_v08.py
- `main()` --calls--> `source_identity()`  [INFERRED]
  validation/ci_v08.py → release/source_identity.py
- `overview()` --calls--> `safe_name()`  [EXTRACTED]
  release/build_complete_release.py → release/verify_complete_release.py
- `main()` --calls--> `validate_policy()`  [EXTRACTED]
  release/build_complete_release.py → release/publication_policy.py
- `main()` --calls--> `safe_name()`  [EXTRACTED]
  release/build_complete_release.py → release/verify_complete_release.py

## Import Cycles
- None detected.

## Communities (10 total, 2 thin omitted)

### Community 0 - "Release 0"
Cohesion: 0.27
Nodes (8): main(), Path, Resolve local Git identity or export metadata; external package verification…, source_identity(), digest(), execute(), main(), Path

### Community 1 - "Release 1"
Cohesion: 0.61
Nodes (7): main(), Path, safe_name(), sha(), validate_contents(), validate_metadata(), verify()

### Community 3 - "Release 3"
Cohesion: 0.48
Nodes (6): git(), info(), json_bytes(), main(), overview(), ZipInfo

### Community 4 - "Release 4"
Cohesion: 0.50
Nodes (4): publication_policy_current(), Path, Publishing a design prerelease never authorizes physical operation., validate_policy()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Not enough signal to generate questions. This usually means the corpus has no AMBIGUOUS edges, no bridge nodes, no INFERRED relationships, and all communities are tightly cohesive. Add more files or run with --mode deep to extract richer edges._