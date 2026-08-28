#set page(paper: "a4", margin: 16mm)
#set text(font: "Noto Sans CJK KR", size: 9pt)
#set heading(numbering: "1.")

= Gate-1 CUT-01 최소수량 coupon 지그 조립도

Revision: `compact-single-path-v0.3` / nominal envelope 415 × 248 × 203 mm

#image("../../../renders/jigs/gate1_assembly.png", width: 88%)

== 구성과 하중경로

CUT-01은 축당 1장, 합계 2장만 쓴다. CUT-04 5 mm screen coupon 1개, CUT-05 shaft 2개, CUT-03 plate 2개, 6004-2RS 4개, DRV-03 lamination 6개, G1J-01/02/P01/P02/P03, 3 mm polycarbonate guard와 0–200 N gauge/load-cell로 구성한다.

고하중 경로는 cutter → metal shaft → 6004 → CUT-03 → G1J-01 metal base → 고정 table이다. Printed chute/tray/corner는 load path가 아니다.

== 조립

1. G1J-01을 table에 M8 4점 체결하고 평면도 0.3 이하를 확인한다.
2. CUT-03/6004/CUT-05를 조립하고 bearing outer ring만 눌러 삽입한다.
3. CUT-01 두 장을 6.5 axial offset으로 interleave하고 0.25–0.50 metal shim으로 gap을 설정한다.
4. CUT-04 screen을 cutter tip 아래 nominal 3.0, 실제 최소 clearance 1.9 이상으로 금속 rail/shim 고정한다.
5. DRV-03을 3장/gear로 dowel 체결한다. 20회 hand rotation에서 접촉 0이어야 한다.
6. G1J-02 shaft centre–force hole을 250.0 ±0.5로 실측한다.
7. Tray/chute/polycarbonate panel과 hard-open guard switch를 설치한다. Torque arm narrow slot 바깥의 offset baffle이 fragment 직선경로를 막아야 한다.
8. Manual torque 시험 후에만 합격 donor drive를 연결한다.

#image("../../../renders/jigs/gate1_exploded.png", width: 88%)

#image("../../../renders/jigs/gate1_rotor_detail.png", width: 78%)

상세 BOM은 `bom.csv`, 시험 입력·계측·CSV schema·pass/fail은 `test_procedure_ko.md`가 controlling이다. Gate-1 signed raw CSV와 사진/영상이 없으면 PASS로 바꾸지 않는다.
