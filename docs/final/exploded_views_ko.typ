#set document(title: "exploded views")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= exploded views
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 조립 순서

Frame → shredder frame → bearing/shaft → cutter stack → phase gear/chain/motor/shear fuse → screen/recirculation/hopper → flake bin → feeder → extruder/thrust → heater/sensor/die → hot shield → cooling → gauge → puller → spooler/traverse → guards → enclosure → wiring → firmware → calibration → dry checks.

각 단계의 형상은 `assembly_drawing_set.pdf` 해당 도면 번호를 사용한다. 고하중 경로는 metal part → bearing/plate → aluminum profile → table이다.
