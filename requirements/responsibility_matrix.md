# 책임·검증 matrix — safety-orchestration-closure-v0.6.1

|영역|Source of truth|자동 증거|물리 증거|Release 상태|
|---|---|---|---|---|
|Envelope/CAD|`cad/parameters/baseline.json`, FreeCAD Python|B-Rep topology, bbox, collision/render|선택적 조립 correlation|DIGITAL PASS|
|Print|FreeCAD solid + slicer profile|mesh manifold, PrusaSlicer 3MF/G-code|coupon/fit check|DIGITAL PASS|
|Shredder load|controller contract + coupled OpenModelica|mandatory scenario 집합의 speed/start/retry/jam/fuse, dynamic envelope|optional Gate-1 correlation|VIRTUAL PHYSICS PASS|
|Structure|OpenModelica envelope → structural script|10 screening + bearing/shaft 각 3단계 CalculiX mesh + frame sensitivity|optional inspection/correlation|VIRTUAL PHYSICS PASS|
|Screw/barrel|16 mm×16D source/drawing|throughput/torque/thermal screening, topology|process coupon, Gate-3/4|RFQ HOLD|
|Firmware|process/fault contracts → generated header + `MachineSupervisor` + Mega adapter|Mega compile, module tests, deterministic production-class runtime traces, EEPROM calibration lock|wired I/O/hard-cut/cooling-current test|SAFETY ORCHESTRATION DIGITAL GATE|
|Cross solver|FreeCAD controlling geometry + OpenModelica envelope|STEP 9/LC10/hash binding/result validator|Autodesk Fusion solve 결과|PENDING EXTERNAL|
|Safety|architecture/process/fault-response contracts|atomic clear/start, purge, common rundown, requalification, dancer prelimit와 false-PASS mutation checks|commissioning E-stop/interlock/fuse/cooling feedback test|DIGITAL GATE / COMMISSIONING APPROVAL REQUIRED|
|Budget|`bom/cash_budget.csv`|target/absolute rollup|donor evidence + supplier quotes|CONDITIONAL|
|Release|manifest + checklist|exact-head clean-clone safety-orchestration/implementation/virtual gates|Fusion/optional empirical evidence|TARGET SAFETY_ORCHESTRATION_BASELINE; CROSS-SOLVER PENDING|

Parent Codex는 architecture, safety, budget, visual review, merge/release acceptance를 소유한다. Subagent 또는 simulation의 PASS는 parent의 source/diff/output 재검토 없이 final acceptance가 아니다.
