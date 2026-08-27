# filament-recycler

PLA 폐출력물과 세척·건조된 PET 용기를 분류, 3단 파쇄, 건조, 압출, 직경제어하여 1.75 mm 필라멘트로 재생하는 모듈형 탁상 장치의 설계 저장소입니다.

현재 상태는 **fabrication review용 설계 패키지 완료 / 물리 release 미승인**입니다. 계산, parametric CAD, firmware/Pi core, 배선 topology와 한국어 문서는 자동 검증되지만 실제 donor 실측과 단계별 물리 시험 전에는 완성 장비로 간주하지 않습니다.

## 핵심 목표

- 명목 처리량 및 안정 연속 처리량을 구분해 보고하며 안정 처리량 200 g/h 이상을 목표로 함
- PLA / PET / UNKNOWN-REJECT 재질 판별과 고정 색상 범주 분류
- 3단 파쇄와 진동식 이송·입도 선별
- 재질별 건조, single-screw 압출, X/Y 비접촉 직경 측정
- puller 폐루프 제어와 표준 1 kg급 spool 권취
- Arduino Mega 안전·실시간 제어와 Raspberry Pi 4 영상처리·로그
- 24 V 600 W 전력 한도, 신규 구매 200,000 KRW 및 CNC 100,000 KRW 목표

## 주요 결과물

- 제작·조립 매뉴얼: `docs/build_manual_ko.pdf`
- 조립 매뉴얼 40-topic 추적표: `docs/manual_coverage.csv`
- 설계·검증 보고서: `docs/design_report_ko.pdf`
- 요구사항/가정/감사표: `requirements/system_requirements.md`, `requirements/assumptions.md`, `requirements/compliance_matrix.md`
- 안전·운전·교정: `docs/safety.md`, `docs/operation.md`, `docs/calibration.md`
- TFT UI 화면·adapter gate: `docs/ui_screens.md`
- CAD source/output: `cad/freecad`, `cad/generation/fcstd`, `exports`, `renders`
- CAD review variants: `renders/review` (section/x-ray/exploded/tool/cable/slicing)
- 배선·pinout/protocol: `electronics/schematics`, `electronics/wiring`, `electronics/pinout`, `electronics/protocol`
- BOM: `bom/bom.csv`, `bom/target_budget_design.csv`, `bom/engineering_recommended_design.csv`, `bom/cost_rollup.csv`
- CNC/RFQ 사전검토: `exports/cnc_quote_packages` (제작 승인도 아님)
- 구조 1D FEA 교차검증: `calculations/structural/beam_fea.md`, `simulation/structural/beam_crosscheck.json`
- 검증 상태: `docs/validation_report_ko.md`, `validation/release_checklist.md`

## 재현·검증

```bash
nix develop --command bash -lc \
  "FreeCADCmd -c \"import runpy; runpy.run_path('cad/generation/generate_all.py', run_name='__main__')\""

QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c \"import runpy; runpy.run_path('cad/generation/render_views.py', run_name='__main__')\""

nix develop --command python3 validation/run_all.py
```

전체 artifact의 크기와 SHA-256는 `artifacts/manifest.json`에 기록됩니다. 200,000 KRW 목표는 safety relay와 camera를 포함한 적합한 project-lab 재고가 확인될 때만 조건부이며, 현재 공개 후보 두 품목만 235,200 KRW입니다.

설계 파일만 보고 cutter, heater 또는 고전류 회로를 바로 제작·가동하지 마십시오. 물리적 안전장치와 합격 시험은 `validation/release_checklist.md`에 따라 별도로 확인해야 합니다.
