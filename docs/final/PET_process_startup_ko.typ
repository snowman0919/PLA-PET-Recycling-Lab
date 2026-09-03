#set document(title: "PET process startup")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= PET process startup
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

확인된 단일 PET lot과 오염·수분 coupon, all-metal hot path, 실제 정격 확인된 300 °C급 wiring/cutoff, calibrated sensors.

== 방법

245/260/270 °C barrel과 265 °C die가 ±5 °C band에 든 뒤 guarded low-feed first-hot-test를 수행한다. PLA 결과를 재사용하지 않는다.

== 증거

Lot/moisture·오염 기록, 온도/압력 징후, relief/leak 영상, X/Y diameter·ovality·U95, 실제 질량/시간.

== 수치 합격기준

Mean diameter error ≤0.05 mm; ovality ≤0.05 mm; U95 ≤0.03 mm; 20개 연속 valid; hot-zone travel ≥1.30 mm; 누설 0건; 3–6 MPa relief coupon 3개 모두 insert 포획 상태로 우회 개방.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
