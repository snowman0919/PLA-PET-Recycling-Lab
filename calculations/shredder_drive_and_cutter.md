# Cycloidal-derived cutter와 구동계 screening

## 형상

각 1/7 pitch에서 capture flank 76%는 `s(u)=u-sin(2*pi*u)/(2*pi)` cycloid displacement로 root radius 18 mm에서 tip radius 29 mm까지 상승한다. 나머지 24%는 짧은 overhung nose와 빠른 cubic relief다. 따라서 기존 4점 saw-tooth polygon이 아니며 FreeCAD source와 CUT-01 DXF가 같은 곡선을 생성한다.

## actuator

Actuator 기준은 특정 part number가 아니라 `INTERCHANGEABLE_DONOR_GEARMOTOR` functional interface다. 18–30 V reversible brushed gearmotor, cutter 환산 continuous 14 N·m, 3 s peak 24 N·m, 20–40 rpm을 Gate-1에서 입증해야 한다. DRV-01 plate와 #35 12T:18T/24T chain, DRV-02 four-bolt hub를 쓰므로 donor가 바뀌면 motor-side bracket/hub만 바뀐다. Catalog 이름만으로 torque를 인정하지 않는다.

PLA/PET 명령은 32/24 rpm, 정상 요구 14 N·m, profile current trip은 16/18 A, 20 A branch fuse, 3회 bounded reverse 뒤 latched fault다. 한 phase gear의 6 x 6 x 4 mm annealed brass key가 nominal 24 N·m 기계 relief이고, 이 torque에서 cutter tip tangential force는 828 N이다. 두 shaft의 반대회전/phase는 generic M3 Z16, 20 degree, face 18 mm 이상 steel pair 또는 DRV-03 3-lamination/gear가 유지한다. Key 전단과 gear 손상 여부는 coupon에서 확인한다.

## 구매/치수 Gate

Project-lab wheelchair/conveyor gearmotor, scooter/e-bike gearmotor, 동급 donor 순으로 조사한다. 정확 model, label, 수량, 상태, shaft, no-load rpm/current, 30분 온도를 기록하기 전 현금 0원으로 확정하지 않는다. Gate-1 PASS 전 full cutter 수량을 발주하지 않는다.
