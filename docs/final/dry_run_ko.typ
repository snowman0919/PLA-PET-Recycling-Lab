#set document(title: "dry run")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= dry run
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== 상태 전이

`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.

== 절차

== 입력

원료 없음, heater fuse 제거, guard 장착, tach/current 계측, branch별 별도 승인.

== 방법

Fan→puller/spooler/traverse→FD-MET feeder→screw→guarded shredder 순으로 한 branch씩 구동한다. 방향·fault pin·tach-loss·limit·E-stop을 강제한다.

== 증거

명령/실측 RPM·전류·방향 표, fault/limit/E-stop timestamp log, 복전·재기동 video.

== 수치 합격기준

명령 반대 회전 0건; feeder 5 A, puller/spooler 각 5 A design envelope 이내; tach-loss 또는 driver fault 뒤 다음 supervisor cycle에서 command 0; traverse usable width 68 mm와 2 mm home backoff; 자동재기동 0건.

== Checklist

- [ ] 작업자·검토자·날짜·장비 ID
- [ ] 입력 조건·측정값·원시 증거 경로
- [ ] Pass/fail 기준과 결과
- [ ] 다음 단계 승인 또는 lockout 복귀
