# 자동검증 보고 — compact-single-path-v0.3

실행일 2026-08-28, 명령 `python3 validation/run_all.py`.

| Gate | 결과 | 증거 |
|---|---|---|
| Engineering calculation | PASS | `simulation/engineering_summary.json` |
| Mega profile lock/change wizard | PASS | host C++ test |
| FreeCAD source/artifact generation | PASS | 12 print families, assembly FCStd/STEP |
| Envelope/collision/load path | PASS | 470 x 700 x 930 mm, `simulation/cad_clearance.json` |
| Render package | PASS | assembly/module/review PNG 13개 재생성·parent visual review |
| 한국어 PDF | PASS | A4 manual 7쪽, report 8쪽 |
| Artifact manifest | PASS | 141개 SHA-256 entry |
| Release consistency | FAIL | exact motor 반영 후 cash cap 초과 |

Exact MY1016Z motor/driver/current sensor/hardened phase gear를 포함한 계획 신규 현금비용은 309,900 KRW로 hard cap을 109,900 KRW 초과한다. 따라서 budget gate는 FAIL이며 main 승격을 금지한다. Shredder 금속 unique family는 CUT-01..08의 8개이고 출력 CAD 질량은 생성 manifest 기준이다. Shredder state의 peak arbiter는 500 W이며 600 W PSU 대비 100 W margin이다. Shredder와 barrel heater/screw는 상호 배제한다.

이 결과는 simulation/CAD/software gate다. 실제 파쇄, 입도, melt flow, 200 g/h, 직경, thermal/pressure response와 safety certification 결과가 아니다. 물리 Gate 1–5는 사용자 승인과 donor measurement 뒤에 남아 있다.

`python3 validation/run_all.py`는 engineering, Mega host test, CAD generation, FreeCAD collision/load path, render package, PDF와 manifest까지 PASS한 뒤 `cash cap exceeded`에서 exit 1로 종료했다. Budget 이외 release test 함수는 별도 실행에서 모두 PASS했다. 현재 Mega 산출물은 host-testable control core이며 exact TFT/pin driver와 실제 BTS7960/ACS758 calibration은 입고품 확정 전 production firmware로 간주하지 않는다.
