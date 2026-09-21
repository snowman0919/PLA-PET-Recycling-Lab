# C2.1 S2 단일 입력·역방향 출력 전동계 핸드오프

## 결론

이 반복은 공용 M1 한 개가 구동하는 고정 링 사이클로이드 입력과 고정축 역회전 출력 후보를 구현했다. 독립 구동 자유도는 1개이고 별도 S2 모터는 없다. 명목 q=8, e=7mm, 입력 +120rpm에서 출력/로터는 -15rpm이다.

현재 통합 결과 상태는 **DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD**다. 구매·가공·통전은 모두 HOLD다. 분쇄 성능 PASS, 정격 coupling, 제조 가능 drivetrain 또는 완성 기계 충돌 PASS를 뜻하지 않는다.

## 2026-09-21 후속 통합

- P0 verifier는 실제 `performance_records.json`, raw/input SHA-256, C2 revision과 candidate geometry hash, cost ledger를 다시 계산한다. 미보정 DEM은 실행 건수에는 포함하지만 qualified 학습 데이터에서는 제외하고 합성 fixture는 실제 건수에서 제외한다.
- 명목 pin/window 0.2mm 여유의 rigid first-contact 평형을 8 input turns, 193자세, 양방향 386건으로 계산했다. 상대 위상 take-up은 0.301558~0.346031도, single-contact force는 출력 1N·m당 26.316~30.015N이며 8N·m 가정에서는 210.53~240.12N이다. 탄성 pin 분담·Hertz 응력·마찰·마모·roller 정격은 HOLD다.
- C2의 실제 생성 STEP인 fixed shear(sensor blind bore 포함), 4mm perforated screen reference, split wear liners, thermal saddles와 전후 caps를 C2.1에 통합했다. rear cap 공간 때문에 coupling/output 구획을 +4mm 이동했다.
- 통합 STEP은 41 solids로 재수입했고 정적 820쌍, q=8 전 주기의 33개 표본 자세 11,360쌍에서 양의 체적 관통 0건이다. 표본 사이 연속 BRep 및 전체 기계 충돌 인증은 아니다.
- CalculiX 2.21 coupon을 PLA/PET 선형 탄성, TPU Neo-Hooke 가정으로 소재별 4/8/16요소, 총 9건 실제 실행했다. 8→16 요소 reaction 변화는 PLA 0.836%, PET 1.036%, TPU 7.740%다. 물성은 미보정 가정이며 fracture/tear/viscoelasticity/S2 접촉/입도/처리량 라벨이 아니다.
- Data 검색으로 확인한 국내 200W BLDC 모터 단품 최저 확인액 중 BL6099-2420은 기본 배송 포함 110,200원으로 전체 100,000원 soft limit를 이미 넘는다. 해외 57BLY110-230의 USD35.50은 배송·세금·driver 없는 base price라 landed quote가 아니다. M1과 전체 원가는 계속 HOLD다.
- P5는 재료/전단금속/외벽·방열판/모터/감속기 5-node 열망으로 확장했다. C2 CAD 체적 기반 가정 열용량과 PLA/PET/TPU별 clean/clogged/fan-failed 반복 batch 총9건, 전류+rpm+온도+buffer fault matrix7건을 실행했다. 이는 미보정 디지털 민감도이며 fan curve·센서 지연·물리 열시험·firmware build/flash·통전은 미실행이다.

## 구현물

- `src/transmission.py`: 좌표계, signed speed, q회전 표시점 반복, 핀/창 offset 운동, 접촉점 속도, 기어 mesh parity, 두 virtual-work 회계.
- `src/build_cad.py`: 입력축/편심 저널, 베어링 envelope, 고정 링 핀과 반력판, 40mm hook/process rotor, C2 전단·perforated screen·wear shells·thermal saddles/caps, 출력 roller/carrier/shaft/support를 갖는 41-object STEP 생성기.
- `tests/test_transmission.py`: e={7,10,14}, q={6,8,16}, 결합 상대속도 독립 FD, XZ/CAD 회전 부호, parity, q회전, virtual work, rigid first-contact 평형, inherited constraints의 11개 회귀.
- `cad/PPR_C2_1_S2_transmission.step`, `_exploded.step`: 실제 생성·재수입 가능한 full/exploded assembly.
- `results/motion_samples.json`: CAD 없이 확인할 수 있는 표시점/shaft 운동 표본.
- `cad/PPR_C2_1_S2_transmission_schematic.svg`: 설명용 schematic이며 생성 CAD section이라고 주장하지 않는다.
- `design/requirements.json`, `bom/transmission_bom.csv`, `docs/ADR-001-S2-TRANSMISSION.md`: 치수, 증거 수준, 대안 비교와 HOLD.

## 핵심 수치

좌표계 F0는 +Y가 축 방향, +X가 전단날 방향, +Z가 위다. 수치 XZ 양의 각(+X→+Z)은 물리적으로 -Y축 회전이므로 CadQuery +Y 회전에는 음의 각을 넣는다.

`E=e[cosθ,sinθ]`, `φ=-θ/q`, `ωout=-ωin/q`다. 출력 핀/창의 diametral stroke는 2e=14mm이고, 명목 roller R5/window R12.2의 0.2mm는 **무간섭 clearance일 뿐 하중 접촉 여유가 아니다**. rotor 좌표에서 coupling 중심 상대속도는 `e|ω|(1+1/q)=98.9601685881mm/s`다.

9개 e/q 조합이 모두 통과했고 최대 독립 속도 FD 오차는 2.6589411510e-08mm/s다. q회전마다 표시점 반복을 검사했다. 명목 CAD-수치 좌표 오차는 4.4408920985e-16mm다. 이상 출력 virtual-work 잔차는 0W, 로터 점 힘/모멘트 power 잔차는 -4.4408920985e-16W다.
## CAD 충돌 검증 범위

축방향 구획은 반력 -34..0mm, process 4..44mm와 caps 0..48mm, coupling 50..64mm, output support 68mm 이후다. inherited 35~45mm 범위 안의 40mm 절삭 폭을 유지했다.

검사 순서는 다음과 같다.

1. 명목 자세의 41개 물체 전쌍 820개를 bbox 선별 후 exact BRep로 검사한다. 충돌 시 JSON 증거를 먼저 쓰고 동적 sweep 전에 실패 종료한다.
2. 정적 통과 후 q=8 입력 전 회전에 걸친 33개 자세에서 움직임 관련 11,360쌍을 bbox 선별 후 BRep로 검사했다. 예상 밖 충돌은 0개다.
3. 전 위상 연속 radial/axial envelope 경계는 보수적 해석식으로 별도 확인했다. hook-shear 0.8mm, hook-screen 0.8mm, hook-thermal 4.2mm, axial compartment 2mm, coupling nominal clearance 0.2mm다.
4. 사이클로이드 고정 핀은 1공전 721자세×profile 1,440점 표본으로 검사했고 최소 sampled clearance는 0.1426475048mm다. q/lobe 대칭은 접촉 기하만 반복하며 표시 hook 주기를 대신하지 않는다.

정적 전쌍만 exhaustive다. 동적 BRep는 33자세 표본이며 자세 사이 연속 충돌을 증명하지 않는다. 해석 envelope는 전 위상 연속이지만 비방사형 세부 BRep를 대신하지 않는다. full-machine collision도 미검증이다.

STEP 재수입은 assembly/exploded 각각 41 solid로 통과했다.

Open CASCADE가 실행 시각을 STEP 헤더에 기록하므로 생성기는 `FILE_NAME` 시각만 고정값으로 정규화한다. 형상 검증 뒤 동일 입력 재실행의 byte SHA-256도 일치해야 한다.

- assembly SHA-256: `9ddfe323c24a46988cef5d43ef3d4c79292f2386ad6002a6780f14d01adec879`
- exploded SHA-256: `f98f39740ccc477d1f7a8b04905dc333e7f86036049f767fe4a674fbe89b6bd2`

## 실제로 남은 HOLD

- 출력 carrier는 역회전 witness/load-extraction 후보다. 0.2mm clearance의 rigid first-contact phase와 단일 접촉 정적 평형은 계산했지만 탄성 핀별 분담과 정격 torque 전달은 검증되지 않았다.
- bearing/roller는 envelope이고 MPN·정격·L10이 없다. 축 피로, 접촉압, fastener preload, 실제 rotor 체결, shoulder/circlip 등 axial retention, 윤활·seal도 미설계다.
- C2 fixed shear sensor bore, perforated screen reference, split wear liners, thermal saddles/caps는 통합했다. screen attachment, sensor mount/wiring/응답, conductive interface, 분리 airflow와 온도 검증은 없다.
- 가드는 section envelope이며 containment 인증 형상이 아니다. E-stop, interlock, 독립 과온 차단 요구는 유지했지만 C2.1 CAD에 완성 통합하지 않았다.
- P5 제어 로직은 독립 과온 체인 feedback을 fail-closed로 감시하지만 E-stop/guard contactor, hardware current limit, manual-reset overtemperature chain과 one-shot thermal fuse의 실제 회로·MPN·배선은 P6 HOLD다.
- PLA/PET/TPU 처리량·토크 이력·입도·체류·jam·에너지는 보정 DEM/실험이 없어 `BLOCKED_PERFORMANCE_DATA`다.
- 모터 미선정, 추가비 landed cost 미완성이다. 미상 원가는 0원이 아니며 100,000KRW 전체 추가비 soft limit 적합성을 주장하지 않는다.
## 재현 명령과 결과

아래는 저장소 루트에서 실행했다. 모든 반환 코드는 0이었다.

```sh
.codex-run/review-env/bin/python validation/pre_push.py
# C1: 14/14
.codex-run/review-env/bin/python c2/src/run_study.py
.codex-run/review-env/bin/python -m unittest discover -s c2/tests -v
# C2: 59/59
.codex-run/review-env/bin/python c2/src/verify_artifacts.py
.codex-run/review-env/bin/python c2/solver/run_coupon_fe.py
# CalculiX coupon: 9/9

.codex-run/review-env/bin/python c2.1/src/transmission.py
.codex-run/review-env/bin/python -m unittest discover -s c2.1/tests -v
# C2.1: 11/11
.codex-run/cad-env/bin/python c2.1/src/build_cad.py
.codex-run/review-env/bin/python c2.1/src/verify_artifacts.py
```

`build_cad.py`는 정적 fail-fast를 먼저 수행하며, 여기서 실패하면 동적 검사를 실행하지 않고 nonzero로 종료한다. 기계 판독 결과와 각 명령 RC는 `results/validation_summary.json`에 있다.

## 이전 독립 검토 종료(커밋 b7cbdb54의 33-object 기준)

부모 검토자는 설계·소스·CAD를 수정하지 않고 커밋 `b7cbdb54670c603a11299881d63de047d3db8d2c`만 독립 재검증했다. `transmission.py`, `build_cad.py`, assembly STEP의 SHA-256은 검토 기록과 일치한다. CAD-kernel 표식 검사는 193자세×3점에서 최대 오차 5.5495161717e-14mm, coupling 독립 FD는 257자세에서 최대 속도 오차 4.5464503273e-9mm/s였다. 재수입 STEP은 33개 valid solid이고 정적 528쌍에서 양의 체적 겹침이 0개였다.

구현 검사는 명목 q8/e7의 q회전에 걸친 **33개 sampled grid 자세·8,800쌍**이고, 부모 검토는 별도의 **15개 nongrid 자세·4,125쌍**에서 겹침 0을 확인했다. 두 표본을 합쳐도 자세 사이의 연속 all-pair 충돌 자유를 인증하지 않는다. 또한 q={6,8,16}, e={7,10,14}의 9개 경우는 수치 궤적 검사일 뿐 9개의 물리적으로 가능한 fixed-ring CAD가 아니다. 조립 CAD 증거는 명목 q8/e7 하나에만 있다.

두 축은 반대 방향이지만 독립 DOF는 하나다. 출력축은 별도 역방향 입력이 아닌 구속된 passive output이고, 공용 M1 한 개·압출 M2·24V 800W PSU/500W cap·100,000KRW 전체 추가비 soft limit·PLA/PET/TPU 및 모든 기존 HOLD를 유지한다. 원본 dirty checkout은 NUL 상태 374개와 binary diff SHA-256 `c8a8bba4ab573345c5767362103b6b5a661b1c1d644d280f4a3e4bad90e30c6a`가 기준과 동일하다. 기계 판독 독립 증거는 `results/independent_review_evidence.json`에 있다.

## Git 및 승인 경계

작업 브랜치는 `codex/c2.1-s2-transmission-20260921`, 기준은 `8e4b44ed8883b0fe84311c55e2fd4caef7cb60e8`이다. 이 문서를 포함하는 커밋과 push/PR 상태는 `git rev-parse HEAD`, 원격 ref와 최종 실행 보고로 식별한다. main/보존 브랜치는 변경하지 않으며 이 산출물은 구매·가공·통전 승인이 아니다.
