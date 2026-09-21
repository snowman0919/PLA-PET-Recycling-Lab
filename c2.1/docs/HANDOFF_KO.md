# C2.1 S2 단일 입력·역방향 출력 전동계 핸드오프

## 결론

이 반복은 공용 M1 한 개가 구동하는 고정 링 사이클로이드 입력과 고정축 역회전 출력 후보를 구현했다. 독립 구동 자유도는 1개이고 별도 S2 모터는 없다. 명목 q=8, e=7mm, 입력 +120rpm에서 출력/로터는 -15rpm이다.

결과 상태는 **KINEMATIC_DIGITAL_PASS_NOT_FABRICATION_RELEASE**다. 구매·가공·통전은 모두 HOLD다. 분쇄 성능 PASS, 정격 coupling, 제조 가능 drivetrain 또는 완성 기계 충돌 PASS를 뜻하지 않는다.

## 구현물

- `src/transmission.py`: 좌표계, signed speed, q회전 표시점 반복, 핀/창 offset 운동, 접촉점 속도, 기어 mesh parity, 두 virtual-work 회계.
- `src/build_cad.py`: 입력축/편심 저널, 베어링 envelope, 고정 링 핀과 반력판, 40mm hook/process rotor, 전단·screen·thermal envelope, 출력 roller/carrier/shaft/support를 갖는 33-object STEP 생성기.
- `tests/test_transmission.py`: e={7,10,14}, q={6,8,16}, 결합 상대속도 독립 FD, XZ/CAD 회전 부호, parity, q회전, virtual work, inherited constraints의 10개 회귀.
- `cad/PPR_C2_1_S2_transmission.step`, `_exploded.step`: 실제 생성·재수입 가능한 full/exploded assembly.
- `results/motion_samples.json`: CAD 없이 확인할 수 있는 표시점/shaft 운동 표본.
- `cad/PPR_C2_1_S2_transmission_schematic.svg`: 설명용 schematic이며 생성 CAD section이라고 주장하지 않는다.
- `design/requirements.json`, `bom/transmission_bom.csv`, `docs/ADR-001-S2-TRANSMISSION.md`: 치수, 증거 수준, 대안 비교와 HOLD.

## 핵심 수치

좌표계 F0는 +Y가 축 방향, +X가 전단날 방향, +Z가 위다. 수치 XZ 양의 각(+X→+Z)은 물리적으로 -Y축 회전이므로 CadQuery +Y 회전에는 음의 각을 넣는다.

`E=e[cosθ,sinθ]`, `φ=-θ/q`, `ωout=-ωin/q`다. 출력 핀/창의 diametral stroke는 2e=14mm이고, 명목 roller R5/window R12.2의 0.2mm는 **무간섭 clearance일 뿐 하중 접촉 여유가 아니다**. rotor 좌표에서 coupling 중심 상대속도는 `e|ω|(1+1/q)=98.9601685881mm/s`다.

9개 e/q 조합이 모두 통과했고 최대 독립 속도 FD 오차는 2.6589411510e-08mm/s다. q회전마다 표시점 반복을 검사했다. 명목 CAD-수치 좌표 오차는 4.4408920985e-16mm다. 이상 출력 virtual-work 잔차는 0W, 로터 점 힘/모멘트 power 잔차는 -4.4408920985e-16W다.
## CAD 충돌 검증 범위

축방향 구획은 반력 -34..2mm, process 4..44mm, coupling 46..60mm, output support 64mm 이후다. inherited 35~45mm 범위 안의 40mm 절삭 폭을 유지했다.

검사 순서는 다음과 같다.

1. 명목 자세의 33개 물체 전쌍 528개를 bbox 선별 후 exact BRep로 검사한다. 충돌 시 JSON 증거를 먼저 쓰고 동적 sweep 전에 실패 종료한다.
2. 정적 통과 후 q=8 입력 전 회전에 걸친 33개 자세에서 움직임 관련 8,800쌍을 bbox 선별 후 BRep로 검사했다. 예상 밖 충돌은 0개다.
3. 전 위상 연속 radial/axial envelope 경계는 보수적 해석식으로 별도 확인했다. hook-shear 0.8mm, hook-screen 0.8mm, hook-thermal 4.2mm, axial compartment 2mm, coupling nominal clearance 0.2mm다.
4. 사이클로이드 고정 핀은 1공전 721자세×profile 1,440점 표본으로 검사했고 최소 sampled clearance는 0.1426475048mm다. q/lobe 대칭은 접촉 기하만 반복하며 표시 hook 주기를 대신하지 않는다.

정적 전쌍만 exhaustive다. 동적 BRep는 33자세 표본이며 자세 사이 연속 충돌을 증명하지 않는다. 해석 envelope는 전 위상 연속이지만 비방사형 세부 BRep를 대신하지 않는다. full-machine collision도 미검증이다.

STEP 재수입은 assembly/exploded 각각 33 solid로 통과했다.

- assembly SHA-256: `10f991b68afee8128a9e9c3d6061c5f4a6907a63f76ea857601bc8e6120b37f6`
- exploded SHA-256: `016840469b97459e7457157cdb87e2a439fe73c91c133aa56685d886a451a10d`

## 실제로 남은 HOLD

- 출력 carrier는 역회전 witness/load-extraction 후보다. 0.2mm 명목 clearance에서 backlash/phase take-up, 핀별 하중 분담과 loaded torque 전달은 검증되지 않았다.
- bearing/roller는 envelope이고 MPN·정격·L10이 없다. 축 피로, 접촉압, fastener preload, 실제 rotor 체결, shoulder/circlip 등 axial retention, 윤활·seal도 미설계다.
- 전단·screen·thermal 물체는 **transmission fixture solid envelope**다. 실제 perforated screen/attachment, 센서 bore/mount/wiring, spreader interface/fins, 분리 airflow와 온도 검증은 없다.
- 가드는 section envelope이며 containment 인증 형상이 아니다. E-stop, interlock, 독립 과온 차단 요구는 유지했지만 C2.1 CAD에 완성 통합하지 않았다.
- PLA/PET/TPU 처리량·토크 이력·입도·체류·jam·에너지는 보정 DEM/실험이 없어 `BLOCKED_PERFORMANCE_DATA`다.
- 모터 미선정, 추가비 landed cost 미완성이다. 미상 원가는 0원이 아니며 100,000KRW 전체 추가비 soft limit 적합성을 주장하지 않는다.
## 재현 명령과 결과

아래는 저장소 루트에서 실행했다. 모든 반환 코드는 0이었다.

```sh
.codex-run/review-env/bin/python validation/pre_push.py
# C1: 14/14
.codex-run/review-env/bin/python c2/src/run_study.py
.codex-run/review-env/bin/python -m unittest discover -s c2/tests -v
# C2: 45/45
.codex-run/review-env/bin/python c2/src/verify_artifacts.py

.codex-run/review-env/bin/python c2.1/src/transmission.py
.codex-run/review-env/bin/python -m unittest discover -s c2.1/tests -v
# C2.1: 10/10
.codex-run/cad-env/bin/python c2.1/src/build_cad.py
.codex-run/review-env/bin/python c2.1/src/verify_artifacts.py
```

`build_cad.py`는 정적 fail-fast를 먼저 수행하며, 여기서 실패하면 동적 검사를 실행하지 않고 nonzero로 종료한다. 기계 판독 결과와 각 명령 RC는 `results/validation_summary.json`에 있다.

## Git 및 승인 경계

작업 브랜치는 `codex/c2.1-s2-transmission-20260921`, 기준은 `8e4b44ed8883b0fe84311c55e2fd4caef7cb60e8`이다. 이 문서를 포함하는 로컬 커밋은 `git rev-parse HEAD`로 식별한다. remote push, merge, main 변경은 하지 않았다. 이 산출물은 구매·가공·통전 승인이 아니다.
