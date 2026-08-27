# Release checklist

## Source와 재현성

- [x] Nix flake와 lock 존재
- [x] baseline FreeCAD generators 실행
- [x] FCStd/STEP/STL 생성
- [x] tolerance coupon print-volume 및 part-separation 자동 검사
- [x] 표준 7-view render 생성
- [ ] 모든 상세 module CAD 생성
- [ ] DXF와 제작도면 생성
- [ ] clean clone에서 전체 재생성

## 해석

- [x] Stage 1 1차 torque/shaft screening
- [ ] Stage 1 detailed cutter/contact FEA와 kinematic phase
- [ ] Stage 2/3, vibration, extruder, thermal, power, control, optical 해석

## 물리 검증

- [ ] donor inventory
- [ ] tolerance coupon 출력·측정
- [ ] cutter coupon torque test
- [ ] interlock/E-stop/thermal fuse fault test
- [ ] 30분 PLA/PET 생산과 직경 통계

## 문서와 비용

- [x] baseline requirements/safety/responsibility
- [x] initial BOM with unknown cost explicitly marked TBD
- [ ] dated vendor pricing and actual CNC quotes
- [ ] Korean build/design PDFs
- [ ] user physical safety approval

현재 release 상태: **NOT READY — 설계 preflight**
