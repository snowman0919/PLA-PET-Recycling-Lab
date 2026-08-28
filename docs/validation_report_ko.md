# 자동검증 보고 — compact-single-path-v0.3

실행일 2026-08-28, 명령 `python3 validation/run_all.py`.

| Gate | 결과 | 증거 |
|---|---|---|
| Engineering calculation | PASS | `simulation/engineering_summary.json` |
| Mega profile lock/change wizard | PASS | host C++ test |
| FreeCAD source/artifact generation | PASS | final-machine, DRV, Gate-1, extruder RFQ FCStd/STEP/STL/DXF |
| Envelope/collision/load path | PASS | 470 x 700 x 930 mm, `simulation/cad_clearance.json` |
| Manufacturing geometry/RFQ | PASS | Gate-1 415 x 248 x 203 mm, CUT-01 gap 0.50 mm, screw 316 mm |
| Render package | PASS | assembly/module/review/Gate-1/RFQ PNG와 parent visual review |
| 한국어 PDF | PASS | manual 7쪽, report 8쪽, RFQ 2쪽, Gate-1 assembly 2쪽 |
| Artifact manifest | PASS | 214개 SHA-256 entry |
| Current-source consistency | PASS | budget arithmetic와 physical release lock 포함 |

조건부 donor 기준 cash scenario는 198,808 KRW로 hard cap 아래 1,192 KRW다. Final-machine 출력 질량은 1100.5 g, Gate-1 시험 jig 출력은 별도 234.1 g/약 4,214 KRW이며 cash rollup에 포함했다. Donor motor는 exact model·수량·상태·label·shaft·current/RPM·30분 온도와 Gate-1 torque 증거가 없어 `UNVERIFIED`다. 따라서 0원은 계획 시나리오일 뿐 final budget acceptance가 아니다.

`validation/physical_gate_status.json`은 Gate-1, screw process coupon과 barrel process coupon을 모두 `NOT_RUN`으로 기록한다. Full cutter order, full screw/barrel order와 `main` 승격은 모두 false다. 자동 package gate가 통과한 사실은 이 물리 잠금을 해제하지 않는다.

Shredder peak arbiter는 500 W이고 600 W PSU margin은 100 W다. Shredder와 barrel heater/screw는 상호 배제한다. E-stop, lid/service hard inhibit, 20 A branch fuse, thermal fuse와 hot/chain guard는 VE에서 제거하지 않았다.

이 결과는 simulation/CAD/software/document gate다. 실제 파쇄 torque, jam, chip size, melt flow, 200 g/h, 직경, thermal/pressure response와 safety certification 결과가 아니다. 현재 Mega 산출물도 host-testable core이며 donor별 BTS7960/current/RPM calibration 전 production firmware가 아니다.
