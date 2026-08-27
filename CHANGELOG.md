# 변경 이력

## Unreleased

- Mega 실제 `.ino`에 PLA/PET dryer PI·상호배제 전력중재와 current/tach/vibration 적응형 jam 복구 경로 연결
- 전체 `.ino` host compile, Pi `DRY_STAGE`/확장 telemetry와 5개 fail-safe commissioning lock 검증
- 43개 요구사항의 증거·물리 미검증·외부 blocker one-to-one 감사표 추가
- 구매/CNC/print/project-lab/donor 및 required/optional을 분리한 비용 rollup 추가
- 34행 CNC/sheet-fabrication DFM·RFQ precheck package 추가
- 7개 load path의 analytic·20-element beam FEA, support reaction·전단·비틀림 조합검증과 review gate 추가
- 21개 section/x-ray/exploded/tool/cable/slicing CAD review variant 추가
- 이전 revision clean clone의 CAD/render/Nix Typst PDF/27-gate 재생성과 byte 재현성 확인
- 조립 PDF에 필수 40개 topic과 81행 BOM·출력/CNC/배선/교정/정비 appendix 수록
- 압출기 insulation 실두께 50 mm 변경, shield/인접 polymer 정상·fault 열저항 gate와 직접 복사 시야 금지 추가
- Release artifact 314개와 자동검증 28-gate 체계로 확장
- 현재 revision clean clone의 CAD/render/Nix Typst PDF/28-gate 재생성과 deterministic artifact 일치 확인
- TFT-independent 9-page UI core, startup/purge interlock, Mega–Pi UI snapshot 계약 추가
- 사용자 요청의 2-tower rack 재범위, 보유 IRLZ44N/camera 조달 처리, concrete render와 draft 문서 정책 기록

## 0.1.0-preflight — 2026-08-28

### Added

- 요구사항, 제약, 가정, 안전·책임 분리 문서
- MIT 및 CERN-OHL-P-2.0 라이선스 구성
- 11-module parametric FreeCAD proof, STEP/STL/DXF와 표준 7-view render
- Stage 1/2/3, sorter, dryer/feeder, 18 mm extruder, forming/gauge/puller와 spooler 계산·simulation
- 이중 gate 입력 classifier, 6색+Reject 저장 diverter와 분리형 grounded control enclosure proof
- Arduino Mega fail-safe control core, FRP1, Pi dual-view/classifier/history supervisor와 host test
- H01–H18 harness, Mega pinout와 firmware 밖 safety-power topology
- 81-line source BOM, 공개 가격 증거, target-budget/engineering-recommended 설계안
- A4 한국어 제작 매뉴얼과 설계·검증 보고서
- 통합 자동검증 runner와 281-artifact SHA-256 manifest
- 독립 clean clone의 CAD/render/PDF 전체 재생성과 22-gate PASS

### Safety status

- 물리 cutter/containment, pressure, mains/24 V panel, optical U95, drying, throughput, diameter와 1 kg winding 승인은 미완료다.
- Revision 0.1.0-preflight는 fabrication review 패키지이며 실제 운전 release가 아니다.
