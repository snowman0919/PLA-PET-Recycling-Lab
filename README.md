# filament-recycler

PLA 폐출력물과 세척·건조된 PET 용기를 분류, 3단 파쇄, 건조, 압출, 직경제어하여 1.75 mm 필라멘트로 재생하는 모듈형 탁상 장치의 설계 저장소입니다.

현재 상태는 **설계 및 검증 준비 단계**입니다. 계산, CAD, 펌웨어와 소프트웨어는 실제 donor 부품 실측과 단계별 물리 시험을 거쳐야 하며, 아직 완성 장비로 검증되지 않았습니다.

## 핵심 목표

- 명목 처리량 및 안정 연속 처리량을 구분해 보고하며 안정 처리량 200 g/h 이상을 목표로 함
- PLA / PET / UNKNOWN-REJECT 재질 판별과 고정 색상 범주 분류
- 3단 파쇄와 진동식 이송·입도 선별
- 재질별 건조, single-screw 압출, X/Y 비접촉 직경 측정
- puller 폐루프 제어와 표준 1 kg급 spool 권취
- Arduino Mega 안전·실시간 제어와 Raspberry Pi 4 영상처리·로그
- 24 V 600 W 전력 한도, 신규 구매 200,000 KRW 및 CNC 100,000 KRW 목표

## 시작점

- 요구사항: `requirements/system_requirements.md`
- 가정과 미확정값: `requirements/assumptions.md`
- 안전: `docs/safety.md`
- donor 조사: `bom/donor_inventory_checklist.md`
- 초기 BOM: `bom/bom.csv`
- Stage 1 계산: `calculations/shredder/stage1_proof_design.md`

설계 파일만 보고 cutter, heater 또는 고전류 회로를 바로 제작·가동하지 마십시오. 물리적 안전장치와 합격 시험은 `validation/release_checklist.md`에 따라 별도로 확인해야 합니다.
