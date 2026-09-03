#set document(title: "shredder commissioning")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= shredder commissioning
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

Gate-1의 정확히 2장 cutter coupon, closed guard, calibrated torque/current/RPM, PLA 1.2/2.0/3.0 mm와 PET body/folded-seam coupon.

== 방법

No-load 뒤 재료별 14 N·m 연속, 18 N·m jam trip, 22 N·m cutter-equivalent shear element를 단계적으로 시험한다. Full stack은 이 gate에서 조립하지 않는다.

== 증거

Torque/current/RPM CSV, jam-stop timestamp, chip-size 사진, shear coupon 파단 사진과 serial.

== 수치 합격기준

PLA 32 rpm/PET 24 rpm 목표의 ±10%; 14 N·m 연속 안정; 18 N·m에서 250 ms 이내 stop; 22 N·m 이하에서 replaceable shear element가 34 N·m phase pair보다 먼저 분리; guard 이탈 0건.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
