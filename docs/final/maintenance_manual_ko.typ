#set document(title: "maintenance manual")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= maintenance manual
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== Lockout

Main disconnect OFF, 0 V, cutter/screw mechanical block, hot zone 60 °C 미만 확인 뒤 작업한다. E-stop만으로 jam을 제거하지 않는다.

== 주기 점검

매 사용 전 guard/interlock/PE/cable/누설; 매 lot cutter clearance·screen·die; 정기적으로 chain tension, bearing play, witness mark, fuse/thermal cutoff, calibration drift를 기록한다. Cutter·gasket·shear fuse replacement 기준은 제조도면과 실측 이력으로 관리한다.
