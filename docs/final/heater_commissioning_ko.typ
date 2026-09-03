#set document(title: "heater commissioning")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= heater commissioning
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

빈 metal hot path, 모든 motor disable, grounded shield, T1–T5 reference probe, 독립 thermal cutoff, 원격 stop.

== 방법

TC open과 permission-open을 먼저 시험하고 zone별 저출력 step으로 channel mapping/온도 상승을 확인한다. PLA 목표 180/195/205/200 °C, PET 245/260/270/265 °C는 별도 ramp로 수행한다.

== 증거

Zone별 command/온도 250 ms log, reference-probe 비교, cutoff 개방 trace, hot-zone travel 측정.

== 수치 합격기준

TC mapping 오류 0건; valid range -20–300 °C; 120 s 가열 명령에서 최소 +4 °C 아니면 fault; command-off 60 s 동안 +8 °C면 fault; software overtemperature 285 °C 이전 차단; cold axial travel ≥1.30 mm.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
