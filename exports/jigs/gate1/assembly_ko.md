# Gate-1 cutter coupon jig 조립도

- revision: `virtual-physics-closure-v0.5.1`
- nominal assembly envelope: `415.0 x 280.0 x 238.0 mm`
- powered configuration envelope: `399.0 x 280.0 x 238.0 mm`
- 목적: CUT-01 두 장만 사용해 PLA/PET peak torque, jam recovery와 chip-size fraction을 측정한다.

## 조립 순서

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. G1J-10 metal foot 네 개에 최종기용 CUT-03 두 장을 체결한 뒤 6004 bearing 네 개와 CUT-08 retainer 두 장을 조립한다. Bearing은 outer ring만 눌러 삽입한다.
3. CUT-05 두 축을 넣고 CUT-01 coupon을 축당 한 장만 6.5 mm offset으로 장착한다. Ø20 split collar와 0.25–0.50 mm metal shim으로 axial gap을 맞춘다.
4. G1J-08 steel angle rail 두 개에 CUT-04 5 mm screen coupon을 captive fastener로 고정하고, cutter tip 아래 nominal 3.0 mm/실제 최소 clearance 1.9 mm 이상을 shim으로 맞춘다.
5. DRV-03 lamination을 gear당 3장, 공통 6 mm key, 2x M4 clamp bolt과 1x Ø3 h6 dowel로 조립하고 hand rotation 20회에서 간섭·shaft 상대 slip이 없어야 한다.
6. G1J-02 torque arm 중심에서 force hole까지 `250.0 ±0.5 mm`를 실측한다. Calibrated handheld force gauge를 M8 clevis에 연결하고 독립 safety tether를 단다. 힘 방향과 arm 운동평면 편차는 2° 이하다.
7. G1J-07 metal upright 4개를 base에 체결한 뒤 G1J-03/04/05/12 3 mm polycarbonate panel을 nylon washer로 유지한다. G1J-12 roof와 G1J-P01 chute 사이 gap은 1 mm 이하, 그 밖의 unguarded opening은 6 mm 이하여야 한다. G1J-06 offset baffle은 right-panel slot에서 10 mm 이상 떨어져 fragment 직선경로를 막아야 한다. G1J-P03은 edge trim일 뿐 panel 지지구가 아니다.
8. G1J-09에 positive-opening S1을 설치하고 `wiring_24v_hardcut.svg`대로 S0/S1→K0→K1 manual-reset hard cut을 배선한다. S0/S1 개방 후 START 없이 자동 재가동하면 FAIL이다.
9. `fastener_schedule.csv`의 torque/witness mark, PE bond <0.1 ohm, panel crack 0을 확인한다.
10. Manual torque test 뒤 main disconnect/shaft lockout에서 G1J-02와 gauge를 제거하고 `gate1_powered_assembly.step` 상태로 DRV-01/검증된 DRV-Axx/DRV-F01/DRV-02/#35 12T:30T를 장착한다. 두 상태를 동시에 조립하지 않는다.
11. Powered 상태에서도 외곽 polycarbonate guard와 S0/S1 hard-cut을 모두 닫고, motor label·shaft·current·RPM·30분 온도 record가 없는 donor는 energize하지 않는다.

고하중 경로는 cutter → metal shaft → 6004/CUT-08 → CUT-03 → G1J-10 → G1J-01 → table이다. Powered 경로는 motor → DRV-Axx/DRV-01/G1J-11 → DRV-F01 → #35 chain/DRV-02 → shaft이며 출력 chute/tray/corner는 하중경로가 아니다.
