# 자동검증 보고 — compact-single-path-v0.3

실행일 2026-08-28, 명령 `python3 validation/run_all.py`.

| Gate | 결과 | 증거 |
|---|---|---|
| Engineering calculation | PASS | `simulation/engineering_summary.json` |
| Mega profile lock/change wizard | PASS | host C++ test |
| FreeCAD source/artifact generation | PASS | 12 print families, assembly FCStd/STEP |
| Envelope/collision/load path | PASS | 470 x 700 x 930 mm, `simulation/cad_clearance.json` |
| Render package | PASS | assembly/module/review PNG 11개 |
| 한국어 PDF | PASS | A4 manual 6쪽, report 7쪽 |
| Artifact manifest | PASS | 104개 SHA-256 entry |
| Release consistency | PASS | revision/stale/cost/print/3MF/PDF checks |

계획 신규 현금비용 189,500 KRW, CNC unique family 8개, 출력 CAD 질량 1,100.5 g다. 24 V peak arbiter는 550 W이며 600 W PSU 대비 50 W margin이다.

이 결과는 simulation/CAD/software gate다. 실제 파쇄, 입도, melt flow, 200 g/h, 직경, thermal/pressure response와 safety certification 결과가 아니다. 물리 Gate 1–5는 사용자 승인과 donor measurement 뒤에 남아 있다.
