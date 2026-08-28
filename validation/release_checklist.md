# Release checklist — compact-single-path-v0.3

## 자동 gate

- [ ] `validation/run_all.py` 전체 통과
- [ ] full assembly <=500 x 750 x 1000 mm, target <=480 x 720 x 950 mm
- [ ] cash budget <=200,000 KRW 또는 exact quote blocker 명시
- [ ] 개별 출력품 <=210 mm, 총 질량 <2.0 kg
- [ ] README/requirements/baseline/BOM/PDF/manifest revision 일치
- [ ] stale architecture 문자열 active source 0
- [ ] FCStd/STEP/STL/3MF/print notes/plate package 존재
- [ ] parent visual review 기록

## 물리 gate — 자동검증과 구분

- [ ] Gate 1 cutter coupon 사용자 승인/실행/결과
- [ ] Gate 2 flake/feed coupon 사용자 승인/실행/결과
- [ ] Gate 3 cold mechanical proof 사용자 승인/실행/결과
- [ ] Gate 4 hot PLA then PET 사용자 승인/실행/결과
- [ ] Gate 5 diameter/full spool 사용자 승인/실행/결과

물리 항목이 비어 있는 동안 branch는 설계 package이며 fabrication/operation release가 아니다.
