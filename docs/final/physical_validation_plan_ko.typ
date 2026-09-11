#set document(title: "physical validation plan")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= physical validation plan
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 이 전이는 실제 장치의 물리 단계에 적용한다. 앞 단계의 서명·측정 증거와 해당 단계의 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다. 문서 작성·호스트 테스트·시뮬레이션의 진행이나 완료를 승인하는 절차는 아니다.

== 절차

== 입력

승인된 coupon/fixture, calibrated instruments, 각 gate 작업자·독립 검토자, lockout/원격 E-stop.

== 방법

P0 23-gate digital prerequisite → P1 inventory/receipt → P2 cold fit → P3 GGM bench → P4 two-cutter coupon → P5 process coupon → P6 cold extruder → P7 safety/logic → P8 motor dry-run → P9 empty hot-zone → P10 PLA → P11 PET → P12 forming/spool 순서로 진행한다. 각 물리 단계는 별도 사용자 승인 전 NOT_RUN이다.

== 증거

Gate별 입력·방법·원시 CSV/사진/video·판정·서명. Simulation 값은 시험 결과 칸에 복사하지 않는다.

== 수치 합격기준

GGM: software gearbox torque limit 8.0 N·m, mechanical protection 8.8–9.3 N·m 실측; cutter는 CUT-01 2개 coupon 선행. Electrical: PE≤0.10 Ω·자동재기동 0. Hot-zone: cold axial travel≥1.50 mm, SYS-04 42.5±0.1 mm/1.50 N·m, 실제 누설은 first-hot-test에서 확인. Forming: diameter/ovality≤0.05 mm, U95≤0.03 mm target; spool: 68 mm traverse, dancer stop 0.36 rad 이전, hard-stop 0.4363 rad 비접촉.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
