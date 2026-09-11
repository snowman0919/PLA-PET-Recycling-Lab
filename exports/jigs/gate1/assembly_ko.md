# Gate-1 cutter coupon jig 조립도 — v0.8 GGM 호환

- manual coupon geometry lineage: `safety-orchestration-closure-v0.6.1`
- current powered drive authority: `validation/physical_v08/physical_gate_contract.json`
- nominal manual assembly envelope: `415.0 x 280.0 x 238.0 mm`
- legacy powered STEP envelope: `399.0 x 280.0 x 238.0 mm` — **reference only, do not energize as current configuration**

## Manual coupon 조립

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. G1J-10 feet에 CUT-03 두 장, CUT-10 seat ring 네 개, 61905/6905 25x42x9 bearing 네 개와 CUT-08 retainer를 조립한다. Outer ring만 press한다.
3. CUT-05/CUT-05R에 CUT-01을 축당 한 장만 장착하고 metal collar/shim으로 axial working gap 0.25–0.50 mm를 맞춘다.
4. CUT-04 5 mm screen coupon은 cutter tip과 실제 최소 1.90 mm clearance를 유지한다.
5. DRV-03/DRV-03R phase gear를 설치하고 tooth phase 11.25±1.0°, hand rotation 20회 무간섭을 확인한다.
6. G1J-02 torque arm의 실제 radius를 250.0±0.5 mm로 측정하고 force gauge/load cell을 독립 tether와 연결한다.
7. 3 mm polycarbonate guard와 roof/baffle를 조립하고 unguarded opening≤6 mm를 확인한다.
8. S0 E-stop/S1 positive-opening interlock hard-cut을 검증한다. 자동 재가동은 허용하지 않는다.

## Powered coupon 변경

Manual torque test 뒤 torque arm을 제거한다. **legacy `gate1_powered_assembly.step`, DRV-01/Axx, DRV-F01 경로는 사용하지 않는다.** Powered coupon은 P3 GGM bench PASS 이후 final GGM shredder path `K9DG60N2+K9G75C → GGM protection coupling → 6201 jackshaft → #35 12T:30T → CUT-05R`를 사용한다. Manual arm과 powered drive는 동시에 장착하지 않는다. 12T/30T는 각각 4x4/6x6 key가 토크를 전달하고, 수령된 sprocket의 maker axial-retention feature가 별도로 축방향 위치를 유지해야 한다. `DRV-02`는 이 경로에서 사용하지 않는다.

고하중 구조경로는 cutter → metal shaft → 61905/CUT-10/CUT-08 → CUT-03 → G1J-10/GGM final support → frame/table이다. 출력 chute/tray/printed trim은 구조 하중경로가 아니다.
