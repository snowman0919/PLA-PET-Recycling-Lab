# 자동 검증 보고서

Revision: `0.1.0-preflight`

실행일: 2026-08-28 (Asia/Seoul)

판정: **자동 설계 검증 PASS / 물리 release 미승인**

## 실행 범위

`nix develop --command python3 validation/run_all.py`가 다음 28개 gate를 순서대로 실행했다.

1. Source BOM 재생성 및 81행/56 CRITICAL/status/가격 증거 검사
2. Dryer power·thermal·feed budget, 압출기/건조기 shield·인접 polymer 정상/고장 열 gate와 metal hot-path geometry
3. Electronics pin collision, H01–H18, 5개 commissioning lock, heartbeat/jam/power timing
4. Extruder diameter sweep·pressure/thrust/drive/heater screening과 geometry clearance
5. Cooling/gauge/puller control model, forming geometry와 spooler shaft/dancer/traverse
6. Vibratory sorter dynamic model과 3-stream geometry
7. Stage 1/2/3 cutter/rotor/screen kinematic clearance
8. Input double-gate/reach probe/7-port와 control-enclosure segregation
9. 전체 FCStd object set, STEP validity, STL facet, DXF marker와 210 mm print gate
10. Arduino Mega portable safety/UI core와 전체 `.ino` host integration compile, startup/purge/UI gate, Raspberry Pi Python 10-test suite
11. 43개 시스템 요구사항의 one-to-one 증거·미검증 gate 추적
12. 34행 CNC/RFQ precheck package의 BOM·STEP·DXF·drawing trace와 미승인 상태
13. 7개 구조 load path의 analytic·20-element beam FEA, support reaction·횡전단·비틀림 조합응력과 intentional review gate
14. Section/x-ray/exploded/tool/cable/slicing 21개 CAD review variant의 크기·구조·한계표기
15. 조립 PDF 필수 40개 topic의 순번·지원파일·실제 PDF text coverage
16. 314개 release artifact의 size/SHA-256 manifest와 112개 7-view PNG
17. A4 한국어 PDF의 header/EOF/page object 구조

최종 marker는 `ALL_AUTOMATED_VALIDATIONS_OK (28 gates)`였다. Manifest는 `artifacts/manifest.json`이며 모든 314개 항목의 현재 bytes와 SHA-256가 재검사됐다.

## 통과가 의미하는 것

- 저장된 계산과 parameter가 문서의 핵심 설계값과 일치한다.
- Proof CAD가 null/invalid shape 없이 export되고 지정된 module/object/DXF 구조를 갖는다.
- Fail-safe software 경로, protocol, logging과 정적 배선 interface가 host 환경에서 일관된다.
- BOM이 미확정 비용을 0원으로 숨기지 않고 target/recommended 전략을 분리한다.
- PDF와 raster review 산출물이 열리고 요구된 한국어 문서가 존재한다.

## 통과가 의미하지 않는 것

다음은 물리 시험과 책임자 승인이 없으므로 모두 OPEN이다.

- Cutter 재료·열처리·FEA·충격 containment와 donor motor dyno
- Screw/barrel/die CNC 공차·재료·열처리, pressure transducer/relief/proof
- Safety relay/contactor/fuse coordination, PE/SCCR/연면거리·열상승과 mains panel 승인
- Camera optic `U95≤0.020 mm`, classifier confusion matrix, gate 1000-cycle
- PET dew point/moisture/degradation, PLA/PET 30분 ≥200 g/h와 diameter/ovality
- 1 kg spool winding/endurance, 전체 frame anchor/tip/vibration
- Landed vendor price, CNC quote와 200,000 KRW budget 달성

따라서 현재 패키지는 fabrication review와 coupon 제작 준비에는 사용할 수 있으나 cutter/heater/high-current energization 또는 production release 근거로 사용할 수 없다.

## 재현 상태

`v0.1.0-preflight` 기준 별도 임시 clean clone의 22-gate와 `52c5b3f` 기준 26-gate에 이어, 현재 revision clean clone에서도 generator→표준/review render→Nix Typst PDF→28-gate 전체 재실행을 요구한다. 최종 clean-clone 결과는 이 변경의 검증 완료 시점에 갱신한다.

STEP header timestamp와 review JSON 경로는 deterministic 값/저장소 상대경로로 정규화한다. STL, DXF, 표준/review render, Nix Typst 0.15.1 PDF, 계산 JSON과 review JSON은 clean clone에서 byte-identical했다. FCStd 51개는 FreeCAD가 생성 시각·UUID·내부 object ID를 기록하므로 형상·object-set 검증은 재현되지만 container byte hash는 실행마다 달라질 수 있다. Manifest는 해당 실행에서 전달되는 실제 파일의 hash를 기록한다.
