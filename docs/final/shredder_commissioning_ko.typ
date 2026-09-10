#set document(title: "shredder commissioning")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= shredder commissioning
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 이 전이는 실제 장치의 물리 단계에 적용한다. 앞 단계의 서명·측정 증거와 해당 단계의 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다. 문서 작성·호스트 테스트·시뮬레이션의 진행이나 완료를 승인하는 절차는 아니다.

== 절차

== 입력

P3 physical release PASS, 정확히 2장 CUT-01 P4 coupon, closed GGM guards, calibrated A0 current/torque/RPM, PLA 1.2/2.0/3.0 mm와 PET body/folded-seam coupon.

== 방법

No-load에서 약 16 rpm cutter speed를 기록한 뒤 P4 재료 coupon을 낮은 투입률로 시험한다. P3에서 보정한 software gearbox torque limit 8.0 N·m가 정상 처리 중 반복되면 feed를 낮추고 원인을 기록하며 보호값을 올리지 않는다. Controlled jam은 bounded reverse 최대 3회 후 미복구 시 latched fault로 끝내고 자동 재시작을 허용하지 않는다. 8.8–9.3 N·m mechanical protection은 P3에서 독립 quasi-static coupon으로 선행 검증한다. Full 12-disc stack은 P4 PASS 전 제작/조립하지 않는다.

== 증거

P3 release/evidence manifest, P4 torque-current-RPM CSV, jam recovery log, chip-size/회수율 기록, guard/interlock 및 손상 검사 사진.

== 수치 합격기준

영구 구조·key·guard 손상 0건; jam retry≤3이고 미복구 3차 실패는 latched fault; 자동 재시작 0건; oversize recirculation≤1; 3–6 mm 질량분율≥70%, >20 mm PET strip≤2%, fines≤15%, 회수율≥95%. P3 mechanical protection은 U95 포함 8.8–9.3 N·m 및 파단 후 자유회전/허브·키 무손상.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
