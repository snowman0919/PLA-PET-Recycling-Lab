#set document(title: "pre power checklist")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= pre power checklist
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

Released BOM/도면, 교정 유효 DMM·절연계·토크렌치, exact donor label, 미통전·lockout 상태.

== 방법

25개 assembly traveler와 witness mark를 대조하고 cutter/screw를 손으로 20회 회전한다. PE, 극성, fuse ID, connector, strain relief를 point-to-point 검사한다.

== 증거

서명 traveler, donor-label 사진, torque/치수표, PE·절연·극성 원시 측정 CSV.

== 수치 합격기준

PE bond 각 경로 ≤0.10 Ω; 전자장치 분리 후 500 VDC 절연 ≥1 MΩ; shaft centre 48.00±0.03 mm; feeder radial clearance 0.20–0.25 mm; screw TIR ≤0.10 mm; 미확정 donor 0건.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
