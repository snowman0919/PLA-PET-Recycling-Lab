#set document(title: "PLA/PET Recycler v0.6.1 safety-orchestration release 보고서")
#set page(paper: "a4", margin: 18mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let box(body) = block(width: 100%, fill: rgb("edf5f8"), stroke: 1pt + rgb("286783"), inset: 8pt, body)
#let warn(body) = block(width: 100%, fill: rgb("fff0e8"), stroke: 1pt + rgb("bd4b2d"), inset: 8pt, body)

#align(center)[
  #text(size: 22pt, weight: "bold")[PLA/PET Recycler v0.6.1]
  #text(size: 15pt)[Safety, purge, forming-chain orchestration closure]
  #v(4mm)
  Revision `safety-orchestration-closure-v0.6.1` · 2026-08-31
]

#box[
Release state: *SAFETY_ORCHESTRATION_BASELINE* \
Implementation: *IMPLEMENTATION_BASELINE* \
Virtual physics: *VIRTUAL_PHYSICS_VALIDATED* \
Cross solver: *CROSS_SOLVER_VALIDATION_PENDING* \
Empirical: *EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN*
]

#warn[본 보고서는 디지털 구현과 선택한 가상 방정식 안의 결과다. 실제 fan airflow, cutter torque, purge 질량, filament 품질, E-stop/interlock/fuse 물리 동작, Autodesk Fusion 결과 또는 안전 인증을 주장하지 않는다. 구매·가공·통전·commissioning은 별도 사용자 승인 전 금지한다.]

= 기준선과 architecture freeze

최종 v0.6 source SHA `60ccd92fe9a7df35b550a2a57649b1263da09d10`을 archive branch/tag로 보존했다. v0.6.1 branch에는 현재 main을 한 번 merge했으며 v0.6 tree reversion은 없다. 기계 architecture와 geometry는 동결했다. FCStd/STEP/STL/3MF/PNG binary는 revision 문자열만 바꾸려고 재생성하지 않았고 경량 metadata에 동일 geometry provenance를 기록했다.

470 × 700 × 930 mm enclosure, 16 mm × 16 L/D screw, 360 W process heater, compact cooling, X/Y gauge, puller, dancer/traverse와 1 kg spool을 유지한다. 출력품 12종은 각 축 210 mm 이하이며 slicer planning mass는 reserve 포함 1,012.70 g이다.

#image("../renders/assembly/compact_full_assembly_isometric.png", width: 94%)

= Firmware safety orchestration

Pure C++ `MachineSupervisor`가 process/material/forming 상태, calibration, start transaction, atomic clear, purge와 spool eligibility를 단일하게 조정하고 `.ino`는 physical I/O, EEPROM, UI adapter 역할만 한다.

- Cold boot material은 `NONE`이고 drive/gauge/current/cooling/temperature readiness를 분리한다. EEPROM v2 magic/version/CRC가 틀리면 record를 zero-sanitize하며 부분 교정이 다른 domain을 ready로 만들지 않는다.
- Shredder는 drive/current/guard/subsystem start가 성공한 뒤에만 `SHREDDING`을 commit한다. Preheat는 온도 ready 뒤에도 별도 operator arm 전 extrusion motion을 시작하지 않는다.
- PREHEAT/PURGE start는 IDLE fan-only probe에서 A4 current feedback 1.5 s 연속 healthy 후에만 commit한다. 3.0 s timeout은 FAULT/all-zero이며 clear가 자동 restart를 만들지 않는다.
- Fault clear는 모든 subsystem의 lockout/guard/thermal/driver preflight 뒤 한 번에 commit한다. 실패하면 어떤 latch도 부분적으로 지우지 않는다.
- 최종 actuator invariant가 false면 production output을 적용하지 않고 FAULT/all-zero로 fail-closed한다.

= Purge와 forming-chain policy

`MAINTENANCE_PURGE`는 이전 material profile을 유지한다. Feed 승인과 독립 waste-path 확인이 모두 fresh guard/temperature/cooling/driver preflight를 통과해야만 `PURGE_RUNNING`에서 bounded screw/feed/puller-to-waste motion을 허용한다. 최소 120 s, 32 screw revolution estimate, 온도 안정, no fault와 시각 확인 뒤 screen/hopper/temperature/final acknowledgement를 순서대로 요구한다. Revolution은 `COMMAND_DERIVED_ESTIMATE_NOT_MEASURED`이며 80 g/120 g도 측정 질량이 아니다.

STOP/PAUSE purge abort는 session을 `PURGE_PREHEAT_REQUIRED`, 성공 완료는 `SCREEN_CLEAN_REQUIRED`로 옮긴다. 둘 다 motion/heater를 끄고 T1–Tdie가 60 °C 이하가 될 때까지 validated fan `COOLDOWN`을 유지한다. E-stop은 별도 즉시 all-zero다.

Gauge/cooling/puller/spooler/dancer/traverse fault는 하나의 `NORMAL → RUNDOWN → THERMAL_HOLD → REQUALIFYING → READY_TO_RETHREAD` policy를 공유하면서 reason은 따로 보존한다. Feeder/spool/traverse는 즉시 off, screw와 fault별 waste puller는 bounded rundown한다. Gauge 20개 연속 sample, U95 ≤0.03 mm, 직경/ovality ≤0.05 mm 각 10 s, puller 비포화, cooling feedback, PLA/PET 26.7/28.6 s transport delay를 만족해도 operator rethread 전 winding은 금지된다.

Dancer threshold는 warning 0.32, controlled stop 0.36, mechanical hard stop 0.4363 rad다. 정상 jam은 hard-stop contact 전 정지해야 하며 contact scenario는 emergency sensitivity로만 분류한다.

= Virtual physics와 power

OpenModelica 1.27.0/MSL 4.0.0 suite는 process arbitration, fan-first start, purge lifecycle, common rundown, cooling recovery, quality requalification, puller tach grace, dancer contact, full coupled melt/forming/spool physics와 E-stop phase를 실행한다. Mandatory 111 scenario가 모두 PASS했고 failure set은 비어 있다. Gauge/cooling/spool fault의 common rundown response latency는 모두 0.1 s, quality violation의 requalification entry→`READY_TO_RETHREAD`는 27.8 s였다. 개별 정량치는 `simulation/openmodelica/results/summary.json`을 source of truth로 한다.

별도 component watt 가정으로 계산한 8개 orchestration power phase는 모두 peak 500 W 이하/reserve 100 W 이상이다. 최대는 `SHREDDING` 477.2 W, 최소 reserve는 122.8 W다. OpenModelica dynamic phase에서도 purge/rundown/thermal hold/requalifying 권한과 component 합계를 각각 검사한다.

Normal Empty/Half/Full spool jam과 dancer prelimit는 mechanical hard stop을 사용하지 않는다. `DancerHardStopSensitivity`만 contact reaction을 별도 보고하며 normal safe behavior가 아니다. Transient forming 결과는 final error만 보지 않고 maximum error, out-of-tolerance duration, recovery time, ovality와 invalid interval의 spool eligibility를 함께 기록한다.

= Runtime, red-team과 재현성

- Firmware host module tests: 7/7 PASS.
- Arduino Mega 2560 compile: PASS.
- Production-linked runtime: 43 scenarios, 116 trace events, invariant failure 0.
- Fixed bounded sequence: 4 seeds × 최대 64 events, PASS.
- False-PASS red-team: 14/14 mutation 검출.
- Generated contract equivalence: 11 process phases, 8 power phases, PASS.
- CAD/mesh/slicer/collision/CalculiX 기준은 동결 geometry에 대해 재검사한다.

최종 commit 뒤 clean clone에서 CI-LIGHT와 CI-FULL을 실행하고 exact commit SHA, artifact count, mismatch count와 scenario count를 `validation/evidence/exact_head_evidence.json`에 결속한다. Self-referential evidence는 release commit을 바꾸지 않도록 commit 밖에서 생성한다.

= Fusion, budget와 gate

FreeCAD controlling source의 STEP 9개와 LC01–LC10은 정확한 v0.6.1 engineering-source SHA, STEP/load/model/OpenModelica-envelope hash에 결속한다. LC01–LC10 모두 `rerun_required=true`, result cell은 비어 있고 Windows validator는 오래된 v0.6 binding을 거부한다. 실제 Fusion solve가 없으므로 `CROSS_SOLVER_VALIDATION_PENDING`이다.

- Conditional plan: 175,729 KRW.
- Cooling-feedback generic allowance: 2,000 KRW.
- Contingency 포함 absolute plan: 195,729 KRW; 계획 여유 4,271 KRW.
- `VERIFIED_PROCUREMENT_BUDGET=NOT_ESTABLISHED`; quote/receipt/donor 실물 증거 없음.
- `PROCUREMENT_APPROVAL_GATE=USER_APPROVAL_REQUIRED`.
- `COMMISSIONING_GATE=USER_APPROVAL_REQUIRED`.

Gate-1 cutter coupon부터 Gate-5 diameter/spool까지는 `OPTIONAL_EMPIRICAL_VALIDATION`이며 현재 미수행이다. 이 릴리스는 `SAFETY_CERTIFIED`, `EMPIRICALLY_VALIDATED`, `PRODUCTION_CERTIFIED`, `CROSS_SOLVER_VALIDATED`가 아니다.
