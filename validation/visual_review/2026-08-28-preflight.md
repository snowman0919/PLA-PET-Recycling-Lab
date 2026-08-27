# Preflight CAD visual review

## VR-001 — tolerance coupon part overlap

- Observed issue: 초기 isometric render에서 comb tab과 coupon base가 겹침
- Evidence image: `tolerance_coupon_before_overlap.png`
- Physical consequence: 한 build plate에서 두 부품이 융합되어 clearance gauge 기능 상실
- Severity: High for coupon usability
- Proposed change: base 최대 Y=70 mm에서 5 mm gap을 두고 tab 시작 Y=75 mm, comb spine Y=93 mm로 이동
- Changed files: `cad/freecad/tolerance_coupon/generate.py`
- Re-rendered evidence: `tolerance_coupon_after_gap.png`
- Status: Fixed in generator; physical print not yet tested

## VR-002 — dryer/control mass outside tower footprint

- Observed issue: assembly skeleton에서 dryer와 control envelope가 tower 오른쪽 filament line 시작부에 놓임
- Evidence image: `renders/assembly/full_assembly_skeleton_isometric.png`
- Physical consequence: 실제 heater, flakes와 enclosure 질량이 cantilever/외부 base에 놓이면 전도 안정성과 service aisle에 불리할 수 있음
- Severity: Medium at envelope stage
- Proposed change: profile inventory와 module mass가 나오면 dryer/control을 낮은 base frame에 결합하고 full spool 상태와 함께 support polygon/center-of-mass 계산
- Changed files: 아직 없음; keep-out skeleton은 위험을 노출하기 위해 유지
- Re-rendered evidence: mass-layout revision에서 필요
- Status: Open

## 검토 한계

현재 assembly module은 keep-out box여서 fastener/tool access, cable route, cutter collision과 실제 print overhang을 판정할 수 없다. 이 항목들은 세부 module CAD 이후 검토한다.
