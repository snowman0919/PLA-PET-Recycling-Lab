# 책임·검증 matrix — coupled-digital-validation-v0.5

|영역|Source of truth|자동 증거|물리 증거|Release 상태|
|---|---|---|---|---|
|Envelope/CAD|`cad/parameters/baseline.json`, FreeCAD Python|B-Rep topology, bbox, collision/render|조립 실측|DIGITAL PASS / PHYSICAL NOT RUN|
|Print|FreeCAD solid + slicer profile|mesh manifold, PrusaSlicer 3MF/G-code|coupon/fit check|DIGITAL PASS|
|Shredder load|baseline torque hierarchy + coupled OpenModelica|32 scenario, dynamic envelope|Gate-1 torque/current/RPM/chip size|SURROGATE ONLY|
|Structure|OpenModelica envelope → structural script|9 screening + 2 CalculiX decks|Gate-1 load 재해석/inspection|DIGITAL PASS|
|Screw/barrel|16 mm×16D source/drawing|throughput/torque/thermal screening, topology|process coupon, Gate-3/4|RFQ HOLD|
|Firmware|baseline → generated header|host tests, torque calibration lock|wired I/O/hard-cut test|DIGITAL PASS|
|Safety|architecture/wiring docs|logic and consistency checks|E-stop/interlock/fuse/thermal test|PHYSICAL PENDING|
|Budget|`bom/cash_budget.csv`|target/absolute rollup|donor evidence + supplier quotes|CONDITIONAL|
|Release|manifest + checklist|clean-clone gate|Gate-1 signed evidence|MAIN PROMOTION LOCKED|

Parent Codex는 architecture, safety, budget, visual review, merge/release acceptance를 소유한다. Subagent 또는 simulation의 PASS는 parent의 source/diff/output 재검토 없이 final acceptance가 아니다.
