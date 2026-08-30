# v0.6 구현·교차 solver 완료 감사

Revision: `implementation-crosssolver-v0.6`

```text
release_state: IMPLEMENTATION_BASELINE
virtual_physics_state: VIRTUAL_PHYSICS_VALIDATED
cross_solver_state: CROSS_SOLVER_VALIDATION_PENDING
empirical_state: EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN
```

## 완료된 디지털 증거

|영역|결과|근거|
|---|---|---|
|Mega firmware|Mega 2560 compile + 5 host-test executable PASS|`validation/results/arduino_mega_compile.json`, firmware tests|
|Material/session|ordered change + explicit confirm + phase arbitration PASS|controller contract/host test|
|OpenModelica|74/74 scenario PASS|`simulation/openmodelica/results/summary.json`|
|동적 하중|21.994 N·m cutter, 20.000 N·m phase, 1.857 kN bearing, 0.603 kN chain|dynamic envelope|
|CalculiX|bearing 1.1644%, shaft 0.3119% mesh convergence PASS|structural screening|
|열전대 bore|blind5.5, ligament 3.4 mm, trip SF 2.16|engineering/structural report|
|Fusion handoff|STEP 9, LC10, study 7, worker/result binding validator|`exports/fusion_validation`, `fusion_worker`|
|예산|conditional 173,729; reserve 포함 193,729 KRW|budget views|

## 미완료 외부·물리 증거

- Autodesk Fusion solve/result: `PENDING_EXTERNAL_EXECUTION`
- Fusion correlation matrix: 빈 결과 cell 유지, `PENDING`
- Project-lab inventory: 사진·라벨·실측 없음, `USER_INSPECTION_REQUIRED`
- RFQ/견적/영수증: 전송·회신 없음, `RFP_READY_NOT_SENT`
- 실제 cutter/extruder/gauge/spool 성능과 안전 commissioning: `NOT_RUN`

따라서 v0.6은 실행 가능한 firmware와 확대된 가상 검증, 외부 solver 재현 패키지를 가진 `IMPLEMENTATION_BASELINE`이다. `CROSS_SOLVER_VALIDATED`, `EMPIRICALLY_VALIDATED`, `SAFETY_CERTIFIED`, `PRODUCTION_CERTIFIED`를 주장하지 않는다. 구매·CNC·통전·최초 powered commissioning은 계속 사용자 승인 대상이다.
