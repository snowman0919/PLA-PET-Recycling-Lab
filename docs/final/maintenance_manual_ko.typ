#set document(title: "maintenance manual")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= maintenance manual
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== Lockout

Main disconnect OFF, 0 V 확인과 재투입 방지, cutter/screw mechanical block 및 사용자 확인 뒤 작업한다. E-stop만으로 jam을 제거하지 않는다. 잔류 압력과 저장 에너지를 해제하고 충분히 냉각한다. 기존 60 °C 기준만으로 접촉 안전을 보증하지 않으며, 온도 표시값만으로 내부 냉각 완료를 판단하지 않는다.

== 주기 점검

매 사용 전 guard/interlock/PE/cable/누설; 매 lot cutter clearance·screen·die; 정기적으로 chain tension, bearing play, witness mark, fuse/thermal cutoff, calibration drift를 기록한다. Cutter·gasket·shear fuse replacement 기준은 제조도면과 실측 이력으로 관리한다.

== Hot-zone 유지판 접근 — 절차 미승인 / HOLD

현재 정식 CAD의 차열판을 단순히 위로 들어내지 않는다. FreeCAD 기준 조립 검사에서 상향 5 mm 위치에 T1–T4 프로브, 히터 리드 및 주변 부품 간섭이 있다. 배선을 당기거나 프로브를 지렛대로 사용하지 않는다. 전기적 분리만으로 금속 sheath가 차열판에서 빠지는 것은 아니다.

유지판 후보의 긴 직선 드라이버 접근은 간섭한다. 차열판이 없는 상태의 짧은 L형 공구 회전 공간 검사는 부분 증거일 뿐, 차열판 탈거·공구 삽입·손 공간을 승인하지 않는다.

12×52 mm 점검창과 28×68×2 mm 덮개는 미채택 후보다. 후보의 덮개 탈거20 mm 및 공구 회전 공간은 명목 CAD 검사에서 간섭이 없지만, 체결품·탈락 방지·PE 본딩·차열 성능은 미검증이다. 이 문서를 근거로 기존 차열판을 절단하거나 후보 부품을 설치하지 않는다.

정비 절차 해제 조건: 채택된 CAD/도면과 부품 목록 일치, 체결품 및 본딩 방식 확정, 실제 공구와 손의 접근·부품 탈거 경로 검증, 물리적 lockout 및 사용자 확인. 재조립 후 차열판/덮개 고정, PE 연속성, 배선 손상·장력, 센서 삽입/고정을 검사하고 해당 시운전 gate를 다시 수행한다. 기록 항목은 작업자·날짜·부품 revision·분리한 커넥터·검사값·미해결 사항·승인자다. 현재 실제 정비 시험은 NOT_RUN이다.
