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
- [x] 조건부 VE 산술 합계 198,808 KRW <=200,000 KRW
- [ ] donor shredder motor exact model/수량/상태/성능 확인

## 물리 gate — 자동검증과 구분

- [ ] Gate 1 cutter coupon 사용자 승인/실행/결과
- [ ] Gate 2 flake/feed coupon 사용자 승인/실행/결과
- [ ] Gate 3 cold mechanical proof 사용자 승인/실행/결과
- [ ] Gate 4 hot PLA then PET 사용자 승인/실행/결과
- [ ] Gate 5 diameter/full spool 사용자 승인/실행/결과

물리 항목이 비어 있는 동안 branch는 설계 package이며 fabrication/operation release가 아니다.

Gate-1이 `PASS`가 아니면 budget/current-source 자동 gate가 모두 통과해도 `main` fast-forward는 금지한다. Full cutter stack과 full EX-SCR-01/EX-BAR-01 발주 상태는 `validation/physical_gate_status.json`의 false lock을 따른다.
