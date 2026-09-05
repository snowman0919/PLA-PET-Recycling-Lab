#set document(title: "physical validation plan")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= physical validation plan
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

승인된 coupon/fixture, calibrated instruments, 각 gate 작업자·독립 검토자, lockout/원격 E-stop.

== 방법

Gate 1 cutter coupon → Gate 2 safety/drive → Gate 3 hot-zone leak/relief → Gate 4 gauge/forming → Gate 5 full spool 순서로 수행하며 FAIL 시 즉시 lockout하고 다음 gate를 금지한다.

== 증거

Gate별 입력·방법·원시 CSV/사진/video·판정·서명. Simulation 값은 시험 결과 칸에 복사하지 않는다.

== 수치 합격기준

G1: 18 N·m trip/22 N·m shear; G2: PE≤0.10 Ω·절연≥1 MΩ·자동재기동 0; G3: relief 3/3 PASS·누설 0; G4: diameter/ovality≤0.05 mm·U95≤0.03 mm; G5: 1 kg nominal spool, 68 mm traverse, dancer stop 0.36 rad 이전, hard-stop 0.4363 rad 비접촉.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
