# Release checklist — Revision 0.1.0-preflight

## Source와 재현성

- [x] Nix flake와 lock 존재
- [x] baseline FreeCAD generators 실행
- [x] FCStd/STEP/STL 생성
- [x] tolerance coupon print-volume 및 part-separation 자동 검사
- [x] 표준 7-view render 생성
- [x] 11개 module의 proof CAD/keep-out 생성
- [x] 현재 proof 범위의 DXF와 제작 주석 생성
- [x] clean clone에서 전체 재생성 및 22-gate 재실행

## 해석

- [x] Stage 1 1차 torque/shaft screening
- [x] Stage 1/2/3 kinematic clearance·shaft screening
- [x] Vibration, dryer/feeder, extruder, forming, spooler, power/control screening
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
- [ ] dated vendor pricing and actual CNC quotes
- [x] Korean build/design PDFs와 시각 렌더 검토
- [ ] user physical safety approval

현재 release 상태: **DESIGN PACKAGE COMPLETE FOR FABRICATION REVIEW — PHYSICAL RELEASE NOT READY**
