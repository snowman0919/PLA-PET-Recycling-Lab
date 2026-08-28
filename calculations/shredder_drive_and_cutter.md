# Cycloidal-derived cutter와 구동계 screening

## 형상

각 1/7 pitch에서 capture flank 76%는 `s(u)=u-sin(2*pi*u)/(2*pi)` cycloid displacement로 root radius 18 mm에서 tip radius 29 mm까지 상승한다. 나머지 24%는 짧은 overhung nose와 빠른 cubic relief다. 따라서 기존 4점 saw-tooth polygon이 아니며 FreeCAD source와 CUT-01 DXF가 같은 곡선을 생성한다.

## actuator

선정 후보는 `MY1016Z-24V-250W-75RPM` brushed geared-DC motor다. 24 V, 250 W, 75 rpm output, raw motor torque 0.98 N·m, integrated ratio 23.2:1, S2:60이다. KTR ROTEX19 98ShA bore17/20 coupling으로 right cutter shaft를 직접 구동하므로 cutter 무부하 최대속도는 75.0 rpm이다. integrated gear 효율 0.65를 적용한 보수적 cutter torque는 14.8 N·m다. 이 값은 catalog 조합계산이며 실제 gearhead 출력토크 보증이 아니다. Gate 1에서 current/torque를 교정한다.

PLA/PET 명령은 32/24 rpm, 정상 요구 14 N·m, profile current trip은 16/18 A, 20 A branch fuse, 3회 bounded reverse 뒤 latched fault다. 한 phase gear의 6 x 6 x 4 mm annealed brass key가 nominal 24 N·m 기계 relief이고, 이 torque에서 cutter tip tangential force는 828 N이다. 두 cutter shaft의 반대회전/phase는 KHK `SS3-16H` M3 Z16 hardened gear pair가 유지한다. Catalog hardened surface durability 28.0 N·m보다 relief를 낮게 두고 coupon에서 실제 전단 torque를 확인한다.

## 구매/치수 Gate

Marketplace의 같은 모델명 제품 간 내부 감속과 shaft drawing이 일관되지 않다. Motor plate는 20/73.5 mm hole-spacing을 포괄하는 slot을 사용하지만, 입고 시 label, 17 x 44 mm shaft, no-load rpm, current, 회전방향을 확인하기 전 coupling과 full cutter를 발주하지 않는다.
