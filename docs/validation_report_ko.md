# 자동 검증 보고서

- Revision: `0.2.0-undergraduate-mvp`
- 실행일: 2026-08-28 (Asia/Seoul)
- 판정: **자동 설계 검증 PASS / 제작·물리 release 미승인**

## 현행 검증 결과

`nix develop -c python3 -u validation/run_all.py`에서 최종 marker `ALL_AUTOMATED_VALIDATIONS_OK (27 gates)`를 확인했다.

주요 통과 항목은 다음과 같다.

- 시스템 BOM 58행, `BUY` 23행, 요구사항 43개의 one-to-one 추적
- 2단 파쇄만 활성: Stage 1 twin-shaft와 기능상 Stage 2인 5 mm screen granulator
- Tower A 500×500×1100 mm, Tower B 850×500×1000 mm, 200 mm gap, 700 mm rail, 전체 2250×500×1100 mm
- 3 L gross/2 L usable batch bin, 약 0.5 kg compact dryer, 100~150 g/h forming 계산
- full-assembly와 control enclosure의 `PURCHASED_PART`, `PCB_RESERVED`, `WIRE_ROUTE`, `PLACEHOLDER` 분리 및 비중첩
- 제어함: Arduino 1대, KACT 1개 placeholder, fuse holder 10개, SSR 4개, heat sink 2개, 190×130 mm PCB 예약영역
- dryer·extruder·forming·spooler·Stage 1·screen granulator FreeCAD geometry와 STEP/STL 산출물
- Arduino Mega core/sketch host compile, E-stop/contactor 감시, 3+1 heater output, bounded jam retry
- CNC/RFQ precheck 22행; 주문·제작 승인 상태가 아님을 검사
- artifact manifest의 파일 크기와 SHA-256 일치

카메라 classifier, 자동 색상 routing, vibratory sorter, 구형 중간 파쇄기, Raspberry Pi, 이전 GPU stability evidence와 구형 PDF coverage는 현행 27개 gate에서 제외했다. 저장소에 남은 관련 파일은 비교 이력이며 MVP 제작 기준이 아니다. `stage3_*`/`GRN-*` 파일명은 과거 추적성을 유지하지만 현행 공정에서는 **Stage 2 granulator**를 뜻한다.

## PASS가 의미하지 않는 것

다음 물리 gate는 OPEN이다.

- cutter 재료·열처리·실하중 torque·파편 containment와 donor motor/driver dyno
- screen 통과율·fines·oversize 질량수지
- dryer 수분 제거, PET 열열화, extruder pressure/relief와 100 g/h 이상 30분 질량수지
- KACT의 실제 DC utilization/차단정격, fuse coordination, 배선 굵기, PE 연속성, 열상승
- E-stop을 누른 상태와 controller fault 상태의 위험전력 제거 시험
- X/Y shadow gauge 교정 불확도와 30분 1.75±0.05 mm 안정성
- landed price, CNC 실견적과 200,000 KRW 신규구매 목표 달성

따라서 현재 패키지는 구조·배치·BOM 검토와 견적 준비에는 사용할 수 있지만 cutter/heater/high-current energization 또는 생산 승인 근거로 사용할 수 없다.

## 재현 명령

```bash
nix develop -c FreeCADCmd -c \
  "import runpy; runpy.run_path('cad/generation/generate_all.py', run_name='__main__')"
QT_QPA_PLATFORM=offscreen nix develop -c FreeCADCmd -c \
  "import runpy; runpy.run_path('cad/generation/render_views.py', run_name='__main__')"
nix develop -c python3 -u validation/run_all.py
```
