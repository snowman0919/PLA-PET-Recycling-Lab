#set document(title: "tolerance and fit guide")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= tolerance and fit guide
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
전체 배치: `GGM-FULL-ASM` / 구동계: `GGM R2`. 기본 조립 투상도는 통합 전 참조이며 최신 전체 배치가 아니다.
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 기준

Source-pinned unified catalog 48행(alias reconciliation 포함): 48 PASS / 0 HOLD. 이 집합의 digital coverage는 calculations/tolerance_stack_final.json의 coverage 상태를 따르며 실물 mating 검증은 NOT_RUN이다.

`exports/final/interface_catalog.csv`가 critical interface별 nominal/tolerance/검사법과 source HOLD를 지배한다. HOLD 또는 NOT_EVALUATED 행은 조립·가공 승인 기준이 아니다. Cutter/blade clearance는 출력 공차가 아닌 ground metal shim으로 조절한다. Bearing seat, die insert, screw/barrel cold/hot clearance, rear datum/front sliding travel을 조립 전 측정한다.

#gate[측정기 ID·교정상태·온도·실측값을 기록하고 허용범위를 벗어나면 임의 rework 대신 source parameter와 도면 revision을 갱신한다.]
