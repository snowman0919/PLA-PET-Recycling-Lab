# v0.5.1 가상 물리 폐쇄 완료 감사

Revision: `virtual-physics-closure-v0.5.1`

현재 판정:

```text
release_state: DIGITAL_FABRICATION_BASELINE
virtual_physics_state: VIRTUAL_PHYSICS_VALIDATED
empirical_state: EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN
```

이 문서는 안전 인증, 실제 성능 측정 또는 생산 인증을 주장하지 않는다. 구매·가공·heater 통전·최초 powered commissioning은 계속 `USER_APPROVAL_REQUIRED`다.

## 형상·제작

| 요구 | 증거 | 상태 |
|---|---|---|
| 470×700×930 mm, hard envelope 이하 | generated assembly/STEP/metadata | PASS |
| closed B-Rep와 manifold mesh | solid topology, mesh checks | PASS |
| 12 print family, 각 축 210 mm 이하 | print interface, PrusaSlicer 2.9.6 actual toolpath | PASS |
| interface coherence | 32-row fabrication interface catalog | PASS |
| assembly collision | 163 objects, 13,203 pairs, intentional 12, unexpected 0 | PASS |
| multimodal review | `visual_review/2026-08-30-virtual-physics-closure-v0.5.1.md` | PASS_DIGITAL |

## 가상 물리·제어

| 계층 | 증거 | 상태 |
|---|---|---|
| process arbitration | shared contract + firmware host tests + Modelica phase scenarios | PASS |
| shredder | coupled motor/gearbox/fuse/chain/phase/load, startup, speed, three-retry jam | PASS |
| extruder | thermal/drive/screw/flow-pressure-torque, hot jam, heater faults | PASS |
| forming | cooling, diameter controller, puller, dancer/traverse/spool and real spool jam | PASS |
| power | normal phases ≤500 W, minimum 100 W reserve, illegal overlap rejected | PASS |
| structure | shaft/plate CalculiX + frame/thrust/thermocouple-bore analytical screens | PASS (virtual) |
| firmware | real Arduino Mega sketch + board config + host tests + `arduino-cli` compile | PASS |
| scenarios | OpenModelica mandatory/useful scenario set | 55/55 PASS |

## 독립 gate

| gate | 상태 | 의미 |
|---|---|---|
| `DESIGN_RELEASE_GATE` | PASS | digital fabrication + virtual physics baseline을 `main`으로 승격 가능 |
| `PROCUREMENT_APPROVAL_GATE` | USER_APPROVAL_REQUIRED | 주문·CNC·motor/heater/safety hardware 구매 미승인 |
| `COMMISSIONING_GATE` | USER_APPROVAL_REQUIRED | heater energization, cutter/screw powered test 미승인 |
| optional empirical Gate-1…5 | OPTIONAL_NOT_RUN | design release나 `main`을 차단하지 않음 |

## 예산과 구성관리

- `CONDITIONAL_PLANNING_BUDGET`: 173,729 KRW
- contingency 포함 absolute plan: 193,729 KRW
- `VERIFIED_PROCUREMENT_BUDGET`: `NOT_ESTABLISHED`; 미확정 항목은 0원 실적으로 간주하지 않음
- v0.5 source/archive/tag commit: `9943b0b6c8148db0fa328c6388e00eca2d90619e`
- 현재 artifact 수의 유일한 canonical 값: `artifacts/manifest.json`의 `artifact_count`
- 최종 commit SHA는 자기참조 hash를 tracked 문서에 고정하지 않고, pushed branch ref와 exact-HEAD clean-clone 실행 기록으로 확정한다.

## 최종 합격 조건

이 감사의 PASS는 exact branch HEAD를 clean clone한 뒤 FreeCAD, slicer, OpenModelica, CalculiX/analytical checks, PDFs와 normalized artifact hashes를 전부 재생성하여 `validation/run_all.py --regenerate-renders`가 통과하고, 같은 commit이 fast-forward로 `main`에 승격된 때 확정된다.
