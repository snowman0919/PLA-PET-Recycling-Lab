#set page(paper: "a4", margin: 16mm)
#set text(font: "Noto Sans CJK KR", size: 9pt)
#set heading(numbering: "1.")

= Gate-1 CUT-01 최소수량 coupon 지그 조립도

Revision: `solid-manifold-openmodelica-v0.4` / nominal envelope 415 × 248 × 203 mm

#image("../../../renders/jigs/gate1_assembly.png", width: 88%)

== 구성과 하중경로

CUT-01은 축당 1장, 합계 2장만 쓴다. CUT-04 5 mm screen coupon 1개, CUT-05 shaft 2개, CUT-03 plate 2개, 6004-2RS 4개, DRV-03 lamination 6개, G1J-01–10/P01–P03, 3 mm polycarbonate guard와 0–200 N gauge/load-cell로 구성한다.

고하중 경로는 cutter → metal shaft → 6004 → CUT-03 → G1J-10 metal feet → G1J-01 metal base → 고정 table이다. Guard fragment 유지는 G1J-07 metal upright가 담당하며 printed chute/tray/edge trim은 load path가 아니다.

== 조립

1. G1J-01을 table에 M8 4점 체결하고 평면도 0.3 이하를 확인한다.
2. G1J-10 foot에 CUT-03/6004/CUT-05를 조립하고 bearing outer ring만 눌러 삽입한다.
3. CUT-01 두 장을 6.5 axial offset으로 interleave하고 0.25–0.50 metal shim으로 gap을 설정한다.
4. CUT-04 screen을 G1J-08 steel rail에 체결하고 cutter tip 아래 nominal 3.0, 실제 최소 clearance 1.9 이상으로 shim 고정한다.
5. DRV-03을 3장/gear, 2x M4 + 1x Ø3 h6 dowel로 체결한다. 20회 hand rotation에서 접촉 0이어야 한다.
6. G1J-02 shaft centre–force hole을 250.0 ±0.5로 실측한다. Handheld gauge를 M8 clevis/safety tether로 잡고 힘 방향 편차를 2 degree 이하로 유지한다.
7. G1J-07 metal upright에 G1J-03/04/05 polycarbonate panel을 nylon washer로 체결하고 G1J-06 offset baffle이 arm slot의 fragment 직선경로를 막는지 확인한다.
8. G1J-09의 positive-opening switch와 E-stop을 아래 hard-cut 회로로 배선한다. Guard/E-stop 개방 후 manual START 없이 K1이 재투입되면 FAIL이다.
9. `fastener_schedule.csv`대로 체결·witness mark를 완료한 뒤 manual torque 시험 후에만 합격 donor drive를 연결한다.

#image("../../../renders/jigs/gate1_exploded.png", width: 88%)

#image("../../../renders/jigs/gate1_rotor_detail.png", width: 78%)

== 독립 hard-cut 배선

#image("wiring_24v_hardcut.svg", width: 96%)

K1은 30 VDC/25 A 이상의 실제 DC breaking rating을 확인한다. K0/K1은 저가 relay 구성이지 인증 safety relay가 아니며, Gate-1 원격 시험·lockout·guard를 대체하지 않는다. Mega는 상태를 감시하지만 S0/S1을 bypass할 수 없다.

상세 BOM은 `bom.csv`, 체결은 `fastener_schedule.csv`, 배선은 `wiring_bom.csv`, 시험·pass/fail은 `test_procedure_ko.md`가 controlling이다. Preflight, force calibration, drive calibration, 25개 torque specimen, PLA/PET 각 3회 jam, PLA/PET chip-size aggregate와 증거 hash는 각각의 전용 CSV에 기록한다. 서로 다른 시험을 한 specimen 행에 합쳐 쓰지 않는다. Gate-1 signed raw CSV와 사진/영상이 없으면 PASS로 바꾸지 않는다.
