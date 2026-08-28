# PLA/PET Recycling Lab — 학부생용 MVP

세척·수동 선별한 PLA/PET를 **2단 파쇄 → 0.5 kg 건조·정량공급 → 단일 스크루 압출 → 2축 직경측정 → 권취**하는 중소형 2타워 설계 저장소입니다.

현재 기준은 `Undergraduate MVP v0.2`이며 제작·고전류 통전·물리 안전시험은 아직 승인되지 않았습니다. 자동 재질/색상 분류기, Raspberry Pi, 진동 선별기와 세 번째 파쇄기는 MVP 범위에서 제외했습니다.

## 확정 구조

- Tower A — 500×500×1100 mm: 수동 투입, 1차 twin-shaft, 2차 5 mm screen granulator, 3 L batch bin
- Tower B — 850×500×1000 mm: 0.5 kg dryer/feeder, extruder, 제어함
- 직선 forming rail — 700 mm: 냉각, LED/photodiode X/Y shadow gauge, puller, spooler
- 타워 간격 — 200 mm; 전체 envelope — 2250×500×1100 mm
- 안정 처리량 목표 — 100~150 g/h
- 제어 — Arduino Mega 1대; 외부 컴퓨터 없이 운전
- 비상정지 — 사용자가 누르는 latching NC mushroom E-stop이 공통 24 V actuator contactor coil을 직접 차단하고 Arduino는 보조접점만 감시

설계·배치·BOM의 현행 요약은 [docs/mvp_design_ko.md](docs/mvp_design_ko.md), 수치 계약은 [requirements/architecture_contract.md](requirements/architecture_contract.md), 부품표는 [bom/bom.csv](bom/bom.csv)를 봅니다.

## 배치 표기

- `PURCHASED_PART`: 실제 후보/보유품을 치수로 배치
- `PCB_RESERVED`: 190×130 mm 감시·인터페이스 PCB 예약영역
- `WIRE_ROUTE`: 전력·히터·모터·센서 덕트 경로
- `PLACEHOLDER`: 접촉기·드라이브처럼 MPN/치수 확정 전 교체 가능한 보수 envelope

이 네 범주는 full-assembly CAD와 제어함 CSV에서 서로 겹치지 않도록 검증합니다. placeholder는 구매 확정이나 제작 승인 부품이 아닙니다.

## 재생성·검증

```bash
nix develop --command bash -lc \
  "FreeCADCmd -c \"import runpy; runpy.run_path('cad/generation/generate_all.py', run_name='__main__')\""

QT_QPA_PLATFORM=offscreen nix develop --command bash -lc \
  "FreeCADCmd -c \"import runpy; runpy.run_path('cad/generation/render_views.py', run_name='__main__')\""

nix develop --command python3 validation/run_all.py
```

구형 3단/Pi 기반 PDF·CAD 파일은 비교 이력일 수 있으며 현행 제작 기준이 아닙니다. cutter, heater, 압력부, 고전류 회로는 [validation/release_checklist.md](validation/release_checklist.md)의 물리 gate를 통과하기 전 제작·가동하지 마십시오.
