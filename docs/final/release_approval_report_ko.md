# v0.8 fabrication candidate 승인 보고서

이 보고서는 디지털 설계 산출물의 폐쇄 결과다. 물리 시험, 안전 인증, 구매·가공·통전·시운전 승인이 아니다.

## 릴리스 식별

- release: `PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION`
- revision: `final-design-fabrication-closure-v0.8`
- branch: `final-design-fabrication-closure-v0.8`
- document/release generator commit: `65f758c4b46b520eafd86cf3667ed249af2fb5f2`
- packaged source commit: ZIP 내부 `00_START_HERE/release_manifest.json`이 지배한다.
- release state: `FABRICATION_CANDIDATE`
- design state: `FINAL_DESIGN_FROZEN`
- physical validation: `NOT_RUN`
- safety certification: `NOT_CERTIFIED`
- procurement gate: `USER_APPROVAL_REQUIRED`
- commissioning gate: `USER_APPROVAL_REQUIRED`
- GitHub release: `NOT_PUBLISHED`

## 계산·시뮬레이션 증거

| 항목 | fine 결과 | 판정 |
|---|---:|---|
| CalculiX LC02 cutter shaft | 변위 0.084041 mm, 응력 73.899 MPa, regional SF 2.402 | PASS |
| CalculiX LC04 actual bearing plate | 변위 0.001261 mm, 응력 6.889 MPa | PASS |
| CalculiX LC05 spool spindle | 변위 0.039569 mm, 응력 19.075 MPa, regional SF 9.305 | PASS |
| CalculiX hot-zone selected C mount | free growth 1.1662 mm, combined stress 83.5 MPa, SF 2.156 | PASS |
| OpenModelica hot-zone | growth 1.166147 mm, travel margin 0.133853 mm, SF 2.155689 | PASS |
| OpenModelica LC09 | radial load 21.238978 N, force/moment residual 0 | PASS |

완전 고정 hot-zone case A의 SF 0.206은 실패했고, 이를 숨기지 않고 rear axial datum + front radial sliding guide로 경계조건과 실제 구조를 수정했다. 모든 값은 선형·명시 경계조건 기반 디지털 결과이며 실제 하중·온도·재료·donor 검증을 대체하지 않는다.

## 산출물 및 gate

- FreeCAD final assembly: 187 bodies, solver-stage STEP 10개와 manufacturing-expanded STEP manifest reimport PASS, tolerance interface 15개
- Vector drawing: 20종 SVG + 20쪽 PDF, drawing register 20행
- Print package: active part 12종, slicer/manifold PASS
- Electrical: vector PDF 8종, wire 10행, connector 10행, fuse 7행
- Manual/commissioning: PDF 15종(매뉴얼 6, 단계별 시운전 9)
- Firmware: Arduino Mega HEX SHA-256 `2147a5105bcc8435e52c5a207cb80794bfe4177c3a4fc97e8a28969bead97e65`
- Release inventory: `13/13 PASS`
- ZIP payload: 236 files, schema/hash/clean extraction PASS
- ZIP SHA-256: `0bfbc16c37065d6dacf3c681442cd49244bfe60a41fdcad5dadf3554ce0a0750`

## 남은 사용자 승인

Exact donor 전압·전류·torque·축경·센서 형식, conductor ampacity, connector와 fuse DC 차단능력은 label·사진·실측으로 확정해야 한다. 구매, CNC/판금 발주, cutter/screw/heater/mains 작업, logic/motor/heater 통전과 물리 Gate 1–5는 각각 명시적 사용자 승인 전 수행하지 않는다.
