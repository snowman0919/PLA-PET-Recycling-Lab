#set document(title: "electrical assembly")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= electrical assembly
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 순서

PE bond → PSU 미통전 설치 → branch fuse → hardwired safety chain → drivers/MOSFET → logic → sensors → cable clamp 순이다. `exports/final/electrical`의 세 CSV와 8개 벡터 PDF를 작업표로 사용한다.

#gate[전원 분리 상태에서 PE continuity, insulation, polarity, fuse/terminal ID, forced-open safety contact를 독립 검사한다.]
