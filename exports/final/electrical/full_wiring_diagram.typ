#set document(title: "full wiring diagram")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= full wiring diagram
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`


== 설계 기준

`24 V / 600 W PSU (25 A)` → main fuse → 분기 보호. Hazardous motion/heater permission은 `E-stop → lid → service guard → independent thermal cutoff → safety contactor`의 hardwired normally-safe chain이다. Mega는 feedback만 읽으며 chain을 우회하지 않는다. Protective earth는 frame과 metal hot shield에 전용 bond한다.

== 통전 전 gate

- exact PSU/driver/MOSFET/fuse/connector 정격과 DC 차단능력 확인
- 각 conductor ampacity·온도·길이·전압강하를 현지 규정과 donor stall current로 재계산
- PE continuity, insulation, polarity, branch isolation, forced-open interlock 시험 기록
- logic-only → motor → heater 순으로 별도 사용자 승인; power restore 자동 재기동 금지

== 배선 기준

모든 active conductor는 `wire_schedule.csv`, connector는 `connector_schedule.csv`, 보호소자는 `fuse_schedule.csv`와 일치해야 한다. Heater/motor와 thermocouple/gauge/tach route를 분리한다.
