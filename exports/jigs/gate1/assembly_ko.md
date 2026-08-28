# Gate-1 cutter coupon jig 조립도

- revision: `compact-single-path-v0.3`
- nominal assembly envelope: `415.0 x 248.0 x 203.0 mm`
- 목적: CUT-01 두 장만 사용해 PLA/PET peak torque, jam recovery와 chip-size fraction을 측정한다.

## 조립 순서

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. 최종기용 CUT-03 두 장과 6004 bearing 네 개를 조립한다. Bearing은 outer ring만 눌러 삽입한다.
3. CUT-05 두 축을 넣고 CUT-01 coupon을 축당 한 장만 6.5 mm offset으로 장착한다. 0.25–0.50 mm metal shim으로 axial gap을 맞춘다.
4. CUT-04 5 mm screen coupon을 cutter tip 아래 nominal 3.0 mm 위치에 금속 rail/shim으로 고정하고 실제 최소 clearance가 1.9 mm 이상인지 확인한다.
5. DRV-03 lamination을 축당 세 장 정렬·dowel 체결하고 hand rotation 20회에서 간섭이 없어야 한다.
6. G1J-02 torque arm 중심에서 force hole까지 `250.0 ±0.5 mm`를 실측한다.
7. Chip tray, feed chute, 3 mm polycarbonate 네 panel과 G1J-P03 corner를 설치한다. Torque arm은 right panel의 좁은 slot만 통과하고 외측 offset baffle이 fragment 직선경로를 막는다. Guard가 열린 동안 motor enable은 hard-open이어야 한다.
8. Manual torque test 뒤에만 donor drive를 DRV-01/#35 chain interface로 연결한다.

고하중 경로는 cutter → metal shaft → 6004 → CUT-03 → G1J-01 → table이다. 출력 chute/tray/corner는 하중경로가 아니다.
