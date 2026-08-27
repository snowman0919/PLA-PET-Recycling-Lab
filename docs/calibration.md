# 초기 calibration 절차

## FDM tolerance coupon

보호 요구사항: 출력 부품의 locating/sliding/flake-exposed clearance를 printer·material별 실측으로 정한다.

1. `exports/stl/tolerance_coupon.stl`을 원래 orientation 그대로 배치한다.
2. 실제 장치에 사용할 printer, nozzle, layer height, wall count와 material로 출력한다.
3. slicer compensation은 최초 시험에서 0으로 두고 설정과 material lot를 기록한다.
4. 냉각 후 base와 comb가 분리되어 있는지 확인한다. 융합되어 있으면 실패다.
5. 0.10~0.50 mm slot에 10 mm nominal tab을 넣어 `삽입 불가 / 압입 / 위치결정 / 원활한 slide / 과도한 유격`을 기록한다.
6. 3.8~4.6 mm hole을 0.01 mm caliper 또는 pin gauge로 두 축 측정한다.
7. 선택값과 raw 측정을 `validation/fabrication_review/tolerance_coupon_measurement.csv`에 기록한다.

현재 parameter는 locating 0.10 mm, general sliding 0.25 mm, flake-exposed 0.40 mm이나 **실제 coupon 전 provisional**이다.

## Diameter gauge

아직 hardware가 없으므로 절차 skeleton만 유지한다. gauge release 전에 traceable diameter의 wire 또는 drill shank를 여러 크기로 측정하고 lens distortion, X/Y scale, threshold sensitivity와 반복성을 보고해야 한다. 단일 1.75 mm 기준 하나만으로 선형성을 주장하지 않는다.
