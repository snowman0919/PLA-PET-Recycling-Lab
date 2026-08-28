# Release checklist — Revision 0.1.0-preflight+unreleased

> 2026-08-28 사용자 요청으로 2-tower rack architecture 재범위가 열렸다. 기존 0.1.0-preflight CAD/PDF는 비교용 draft이며 fabrication baseline이 아니다. `docs/user_direction_2026-08-28.md`를 우선한다.

## Source와 재현성

- [x] Nix flake와 lock 존재
- [x] baseline FreeCAD generators 실행
- [x] FCStd/STEP/STL 생성
- [x] tolerance coupon print-volume 및 part-separation 자동 검사
- [x] 표준 7-view render 생성
- [x] section/x-ray/exploded/tool/cable/slicing review variant 생성
- [x] 11개 module의 proof CAD/keep-out 생성
- [x] Control enclosure의 selected·exact-MPN qualification candidate·PCB reserved·user inventory·TBD placeholder·4개 wiring route class 분리
- [x] 현재 proof 범위의 DXF와 제작 주석 생성
- [x] 현재 33-gate clean clone 전체 재실행

## 해석

- [x] 2-tower footprint/height/shelf pitch/MVP stage·bin 수 architecture contract lock
- [x] Tower A 전도·anchor·shelf joint·8 Hz vibration 가상 재검토
- [x] Tower B 수평 cooling/gauge/puller 길이와 service path CAD/contract 재검토
- [x] Stage 1 1차 torque/shaft screening
- [x] Stage 1/2/3 kinematic clearance·shaft screening
- [x] Vibration, dryer/feeder, extruder, forming, spooler, power/control screening
- [x] 7개 load path의 analytic·1D beam FEA 교차검증
- [x] Stage 1 실제 CAD 치근/키홈 3D 선형 정적 FEA와 2단계 mesh convergence
- [ ] Stage 1 detailed cutter/contact FEA와 모든 최종 load case
- [ ] Optical U95와 실제 material/control plant cross-check

## 물리 검증

- [ ] donor inventory
- [ ] tolerance coupon 출력·측정
- [ ] cutter coupon torque test
- [ ] interlock/E-stop/thermal fuse fault test
- [ ] pressure transducer/relief와 grounded panel 승인
- [ ] classifier 1000-cycle·material confusion matrix·7-port routing
- [ ] dryer dew point/moisture와 1 kg spool endurance
- [ ] 30분 PLA/PET 생산과 직경 통계

## 문서와 비용

- [x] baseline requirements/safety/responsibility
- [x] initial BOM with unknown cost explicitly marked TBD
- [x] 공개 후보 가격 증거와 target/recommended BOM 분리
- [x] BUY 32행 구매처 routing과 DigiKey·디바이스마트·Mouser·Playwright AliExpress 후보 증거
- [x] 43개 요구사항 감사표와 34행 CNC/RFQ precheck package
- [ ] dated vendor pricing and actual CNC quotes
- [x] Korean build/design PDFs와 시각 렌더 검토
- [x] 조립 PDF 필수 40개 topic과 전체 85행 BOM 및 control-enclosure layout source 추적
- [ ] user physical safety approval

현재 release 상태: **ARCHITECTURE RESCOPE IN PROGRESS — FABRICATION / PHYSICAL RELEASE NOT READY**
