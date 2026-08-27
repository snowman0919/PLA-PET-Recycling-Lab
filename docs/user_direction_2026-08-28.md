# 사용자 방향성 변경 요청 — 2026-08-28

상태: **quantified architecture contract issued / physical and donor validation open**
적용 대상: 다음 아키텍처 revision, KiCad PCB, BOM 조달 분류, CAD·render 전략, GPU 가상검증, 문서 release 정책

이 문서는 사용자가 2026-08-28에 제시한 방향을 현재 설계에 반영하기 위한 변경 입력이다. 기존 2.295 m 직선형 proof CAD와 0.1.0-preflight PDF를 fabrication baseline으로 승인하지 않는다. 계산·코드·기존 CAD는 비교용 증거로 보존하되, 아래 architecture review가 끝나기 전 신규 제작도·조립도·발주 package를 동결한다.

## 1. 시스템 축소와 2-tower rack 제안

사용자 제안은 전체 시스템을 두 개의 독립 profile rack으로 재구성하는 것이다.

### Tower A — 분류·파쇄

- 상단: 투입 검사, camera/backlight, PLA/PET/UNKNOWN과 color 판정
- 중단: guarded singulator와 Stage 1/2/3 파쇄 모듈
- 하단: vibratory screen, Oversize/Acceptable/Fines 수거와 밀폐 batch bin
- 모듈 사이: 낙하식 chute를 우선하고, 먼지·파편 역류를 막는 removable boot와 service isolation 적용

### Tower B — 재활용·재생산

- 상단/중단: batch bin docking, dryer, load-cell hopper, metering feeder
- 하단: extruder/hot zone과 control/power enclosure를 무게중심이 낮게 배치
- 측면 수평 rail: cooling, dual-view gauge, puller
- 하단 또는 말단: dancer/traverse spooler

두 tower는 sealed removable batch bin과 keyed electrical/data connector로 연결한다. Tower A의 진동·분진을 Tower B의 optics/hot-zone에서 분리하고, 한 tower를 정비할 때 다른 tower의 위험 에너지가 자동으로 따라 켜지지 않도록 isolation boundary를 둔다.

### 이 구성이 유리한 점

- 11개 모듈을 두 개의 설치·정비 단위로 묶어 footprint와 배선 복잡도를 줄일 수 있다.
- 무거운 cutter, motor, extruder를 낮은 rack floor에 두고 금속 shelf→profile→table 하중경로를 만들 수 있다.
- 분류/파쇄와 건조/압출의 먼지·진동·열 영역을 분리할 수 있다.
- batch bin을 물리적 material-lot 경계로 사용해 purge·이력 추적이 쉬워진다.

### 바로 확정하면 안 되는 점

- 용융 직후 filament는 충분히 냉각되기 전 작은 radius로 꺾으면 안 된다. Tower B를 순수 수직 흐름으로 만들지 말고 cooling/gauge/puller는 수평 service rail로 유지한다.
- Tower A의 vertical stack은 무게중심, cutter 반력, 8 Hz sorter 진동과 전도 위험을 키운다. 바닥 고정, rear brace, shelf plate와 tower modal/anchor 검토가 선행돼야 한다.
- 상단 투입구가 높아지면 작업자 reach와 anti-reach chute가 충돌한다. 최대 전체 높이와 투입 높이를 사용자 신체조건·작업대 높이로 잠가야 한다.
- 낙하 chute가 길어지면 flake hold-up, 색상 교차오염, 청소 dead zone이 늘 수 있다. 모든 chute/boot의 탈착·가시성·청소 접근을 CAD에서 증명해야 한다.
- 3단 파쇄를 그대로 유지하면 외형만 두 tower로 묶일 뿐 비용·부품 수가 충분히 줄지 않을 수 있다. MVP에서 Stage 통합 또는 color routing 단순화가 가능한지는 실제 입도·토크 coupon 후 결정한다.

### Parent Codex가 먼저 잠글 결정

1. 두 tower의 허용 footprint, 최대 높이, shelf pitch와 table/anchor 조건
2. Tower A에서 3단 파쇄를 유지할지, 2-stage MVP로 축소할지
3. 초기 MVP의 color bin을 6+Reject로 유지할지, material+Reject만 먼저 구현할지
4. Tower B cooling 직선 길이와 spooler 배치
5. removable batch bin의 용량, 최대 질량, keyed docking과 contamination gate
6. tower별 독립 E-stop/guard zone과 공통 control enclosure의 위치

위 6개 항목의 현재 수치 결정은 `requirements/architecture_contract.md`에 잠갔다. Tower A는 600×600×1350 mm, Tower B는 900×600×1150 mm와 die 이후 760 mm 직선 rail이다. 수동 sealed 8 L gross/6 L usable batch bin, 공통 E-stop chain, tower별 monitored hazardous-energy branch와 공통 제어함 1개를 기준으로 한다. 원문 최종 합격기준 때문에 3단 파쇄와 6색+Reject는 release 구성에 남기며, 2-stage/material-only는 commissioning 비교 모드로만 허용한다.

### 사이드 프로젝트용 최소화 원칙

목표는 가능한 기능을 모두 넣는 것이 아니라 **요구사항 추적표의 필수 end-to-end acceptance를 만족하는 가장 작은 시스템**이다. 모든 module, 자동화, sensor와 custom part는 대응하는 필수 요구사항 또는 실패위험 저감 근거가 없으면 MVP에서 제외한다.

- profile 규격, shelf 폭과 fastener 종류를 가능한 한 통일하고 보유품/COTS/donor를 우선한다.
- 초기 MVP는 수동 sealed batch-bin 이송, material+Reject 최소 bin, 2-stage shredding을 기본 비교안으로 삼는다. Stage 3, 다색 자동 routing과 자동 docking은 계산·가상검증·coupon이 필요성을 입증할 때만 복원한다.
- controller, enclosure와 harness는 tower마다 중복하지 말고 공통 제어함 1개와 최소 connector 수를 우선 검토한다.
- optics는 분류와 직경측정의 요구 해상도·시야·동시운전이 허용할 때만 공유한다. 공유가 성능을 떨어뜨리면 camera 2개를 유지한다.
- `nice-to-have`, 원격 dashboard, 과도한 자동 세척/추적 기능은 end-to-end 재생 필라멘트가 먼저 나온 뒤 backlog로 돌린다.

## 2. 보유품과 BOM 처리 원칙

사용자는 IRLZ44N MOSFET을 다수 보유하고 있으며 “Picamera2 관련 부품”도 충분하다고 밝혔다.

조달 BOM에서는 검증된 보유품을 신규 구매비에서 제외한다. 그러나 assembly master BOM에서 안전·배선에 필요한 부품 행 자체를 삭제하지 않는다. 삭제하면 수량, 전압, 방열, connector, 검사와 대체품 추적이 사라지므로 `USER_STOCK/REUSE`, 현금 구매가 `0`, replacement value `TBD`, 상태 `NEEDS_INVENTORY/NEEDS_QUALIFICATION`으로 관리한다.

### IRLZ44N 주의사항

- 보유 수량, 제조사, lot, genuine 여부, package, 손상과 static test를 먼저 기록한다.
- IRLZ44N 보유는 `ELE-HTR-DRV` 6-channel isolated/default-off driver assembly가 완성됐다는 뜻이 아니다.
- 24 V heater branch에는 gate pulldown, 적절한 gate drive, isolation 요구, fuse, thermal fuse, heatsink, creepage/clearance와 stuck-on fault test가 별도로 필요하다.
- Arduino 5 V pin 직결이나 breadboard 고전류 배선은 허용하지 않는다. 실제 RDS(on), 온도상승과 SOA를 worst-case gate voltage/current로 검증한 뒤에만 channel BOM의 구매 대체로 인정한다.

### “Picamera2” 모호성

`Picamera2`는 Raspberry Pi camera software library 이름이며 BOM에서 제외할 물리 부품명이 아니다. 사용자가 보유한 것이 Camera Module 3, HQ Camera, USB camera, lens, CSI cable, backlight 중 무엇인지 exact model/quantity/photo로 구분해야 한다.

- `GAU-CAM-001` Camera Module 3가 실제 보유·정상이라면 신규 구매 floor 35,000 KRW를 제거하고 `USER_STOCK`으로 전환한다.
- `INP-CAM-001` 분류 camera는 diameter gauge camera와 별도인지 확인한다. 한 camera 공유는 optical geometry와 동시 운전 요구 때문에 자동 가정하지 않는다.
- Picamera2 library 자체는 software dependency/lock file에서 관리하며 hardware BOM 가격 행이 아니다.

기존 가격표의 200,200 KRW Dold safety relay는 하나의 신규구매 후보일 뿐 필수 지정품이 아니다. 작업실에 이미 있는 safety relay/contactor, fused supply, guard, lockout 장비를 사진·모델·정격·상태로 inventory하여 요구 안전기능을 충족하는 보유품은 `USER_STOCK`으로 전환한다. 인증/정격이 확인되지 않은 일반 relay나 IRLZ44N 하나로 안전기능을 대체해 숫자만 맞추지는 않는다.

## 3. KiCad CLI/MCP 기반 최소 PCB 설계

Markdown block diagram과 배선표는 설명 자료이지 최종 전자설계 source of truth가 아니다. Parent Codex는 architecture contract가 잠기면 KiCad 9 project를 만들고, 다음 최소 산출물을 저장소에서 추적한다.

- `.kicad_pro`, 계층형 `.kicad_sch`, `.kicad_pcb`, 필요한 project symbol/footprint library
- MPN, Manufacturer, `USER_STOCK/BUY/DNP`, BOM Comments를 symbol property에 기록한 BOM source
- 전원입력·분기 fuse, logic power, sensor/actuator connector, gate drive/default-off, flyback/TVS, current/temperature feedback와 service/test point
- 실제 enclosure/profile/terminal 치수와 일치하는 board outline, mounting hole, connector 방향, creepage/clearance 및 고전류 net class

PCB도 최소화한다. 먼저 COTS module+terminal wiring과 **단일 carrier/power-control PCB 1장**을 비용·배선복잡도·수리성으로 비교하고, PCB가 실질적으로 줄이는 위험과 배선이 있을 때만 제작한다. Raspberry Pi/Arduino, 보유 MOSFET과 camera module을 불필요하게 재설계하지 않는다. 안전기능 전체를 custom PCB로 재발명하지 말고 작업실 보유 safety hardware와 연결되는 dry-contact/EDM/interface만 필요한 만큼 제공한다.

재현 가능한 검증의 기준은 `kicad-cli`로 둔다. 사용 가능한 KiCad MCP는 schematic/layout 편집과 시각 검토에 활용하되, MCP 전용 상태를 source of truth로 만들지 않는다.

1. `kicad-cli sch erc`와 `kicad-cli pcb drc`를 매 revision 실행하고 report를 남긴다.
2. schematic/PCB analyzer, raw-file·datasheet pin mapping 교차검토를 수행한다.
3. schematic과 PCB가 모두 있으면 cross-analysis, EMC pre-compliance, thermal analysis를 수행한다.
4. `ngspice` 등 simulator가 설치되면 power/gate/sensor subcircuit를 SPICE 검증한다. 미설치 시 생략 사실을 기록한다.
5. Gerber/drill/position/BOM은 architecture와 electrical review가 닫힌 뒤 생성하며, 주문은 사용자 승인 전 진행하지 않는다.
6. ERC/DRC 통과는 제작 승인과 동일하지 않다. critical MPN datasheet와 symbol-pin/footprint-pad mapping을 별도로 확인한다.

## 4. 안전을 병목으로 만들지 않는 적용 원칙

이 장비는 개인 작업실의 사이드 프로젝트이며, 작업실에 안전장비와 여러 차단 수단이 이미 구비되어 있다는 사용자 조건을 설계 입력으로 인정한다. 따라서 특정 고가 안전 릴레이 신규구매를 architecture 선행조건으로 고정하지 않는다.

- 먼저 보유 E-stop, safety relay/contactor, main disconnect, fused PSU, thermal cutoff, guard/interlock, LOTO와 PPE의 모델·정격·상태·사용 가능 채널을 inventory한다.
- 확인된 작업실 장비로 필요한 기능을 충족하면 기계에는 최소 interface와 배선만 추가하고 신규구매를 피한다.
- 안전 검토는 위험별로 `existing workshop control / machine-integrated control / operating procedure / residual risk`를 배정하는 짧은 hazard table로 제한한다.
- E-stop, lid/service interlock, heater over-temperature와 branch fuse는 단일 MCU·단일 software·단일 IRLZ44N에만 의존하지 않는다는 저장소 규칙은 유지한다.
- PPE와 외부 LOTO는 유효한 추가 방호지만, 접근 가능한 회전 cutter나 무감시 heater의 유일한 방호로 계산하지 않는다.
- 안전 논의가 상세 설계를 무기한 막지 않도록, unresolved item은 필요한 interface envelope와 검증 coupon만 정의하고 나머지 기계·PCB 설계를 병행한다.

즉, 안전 목표는 유지하되 **보유 작업실 인프라를 먼저 credit하고, 필요한 최소한만 기계에 통합**한다. 특정 고가 부품이 없다는 이유만으로 전체 프로젝트를 정지시키지 않는다.

## 5. RTX 3080을 사용한 가상 물리 검증

Parent Codex는 현재 가용한 NVIDIA GeForce RTX 3080 10 GB를 직접 사용해 설계 iteration마다 결정가치가 큰 가상 물리 검증을 수행한다. GPU 이름을 보고서에 적는 것만으로 완료 처리하지 말고, 실제 solver process의 GPU 사용 증거와 실행 명령을 남긴다.

우선순위는 다음과 같다.

1. Tower A: cutter/shaft의 torque·접촉 하중 sweep, chute 막힘과 particle residence, vibratory sorting의 입도별 통과율, tower modal/anchor 응답
2. Tower B: dryer/insulation/guard 온도장, melt-zone 열전달과 pressure sensitivity, cooling path와 filament solidification, puller/spooler tension transient
3. 통합: center-of-mass/전도 margin, module removal load case, guard/door collision, cable·hose service envelope

GPU 가속이 실제 이득을 주는 DEM/rigid-body, transient thermal/flow와 Monte Carlo parameter sweep은 CUDA 지원 solver 또는 CUDA 기반 수치도구를 사용한다. 검증된 CPU FEA/SPICE가 더 적합한 항목은 억지로 GPU solver로 바꾸지 말고, GPU를 mesh/parameter sweep과 후처리에 병행 사용한다.

각 run에는 geometry revision/hash, material model, 가정·경계조건, mesh/particle resolution, timestep, solver/version, GPU 모델, random seed, 불확실성 범위, analytic/CPU 교차검산, acceptance criterion과 결과를 기록한다. coarse/fine convergence 또는 timestep sensitivity가 없는 예쁜 animation은 검증으로 채택하지 않는다.

결과 표기는 반드시 `VIRTUAL/SIMULATION EVIDENCE`로 하고 실제 물리시험 완료와 구분한다. 가상검증의 목적은 설계안을 줄이고 위험한 후보를 제거하며 필요한 coupon 수를 최소화하는 것이다. donor 정격, blade 절삭, 실제 polymer 오염·수분, 장시간 열화와 최종 E-stop/interlock 동작은 사용자의 작업실 물리시험으로만 닫는다.

## 6. 원격 저장소

사용자는 GitHub CLI login을 완료했다. 2026-08-28 확인 결과 `snowman0919` API 인증이 성공하고 token의 Contents 권한도 read/write이며, 현재 local repository에는 remote가 없고 `snowman0919/PPR`도 아직 존재하지 않는다. 즉 `gh`를 기술적으로 사용하지 못하는 상태가 아니다. 외부 저장소 생성·remote 설정·초기 push를 parent Codex가 소유한다는 작업 경계 때문에 side conversation에서 실행하지 않았을 뿐이다.

권장 기본값:

- repository: `snowman0919/PPR`
- visibility: `private`
- remote: `origin`
- 초기 push 전 확인: `.env`/token/cache/order temp 부재, licensing 범위, clean worktree, 전체 validation PASS

Parent Codex는 secret scan과 licensing 확인 후 아래와 동등한 명령으로 private 저장소를 생성하고 main을 push한다.

```bash
gh repo create snowman0919/PPR --private --source=. --remote=origin --push
```

이 단계는 더 이상 인증 blocker로 남기지 않는다. 공개 전환은 hardware/CAD license, 안전 면책, third-party asset을 별도 review한 뒤 수행한다.

## 7. CAD/render 구체화 요구

현재 render는 keep-out/proof geometry를 보여 주는 수준이라 제작 판단에 너무 추상적이다. 다음 revision에서는 예쁜 외관보다 조립·정비·위험 판단에 필요한 구체성을 우선한다.

- 실제 profile cross-section, shelf plate, corner bracket, anchor, fastener와 bearing housing
- motor/gearbox/shaft/coupling, cutter spacer/shim/retainer와 guard fastener
- hopper/chute/boot/bin의 벽두께, flange, gasket, latch와 분리 방향
- heater band, sensor boss, insulation, metal shield, pressure relief discharge와 purge catch
- control enclosure, DIN rail, gland, cable duct, PE stud, moving cable와 connector service loop
- cooling duct, camera/lens/light/mirror/window, puller nip, dancer/traverse와 full spool
- exploded view에 Part ID, 순서, fastener와 tool-access 방향
- section view의 열린 면 cap, 절단 hatch, hidden-line 구분과 치수/datum
- 사람/작업대 scale, door/guard sweep, module removal envelope와 center-of-mass/anchor 표시
- print part와 metal part를 재료 색으로 구분하고 “proof envelope”를 실제 부품처럼 보이게 렌더하지 않기

구체 render는 sourced MPN과 실제 치수 없이 임의 형상을 꾸미지 않는다. Donor/stock 식별 전에는 placeholder를 유지하되 각 placeholder에 `UNSELECTED ENVELOPE` label과 필요한 입력값을 표시한다.

## 8. 설계·조립 문서의 현재 위치

사용자의 지적이 맞다. 현재 architecture, donor, 상세 가공도와 물리 coupon이 열려 있는데 `제작·조립 매뉴얼`을 완성본처럼 제시한 것은 시기상조다.

기존 PDF를 만든 합리적 목적은 요구사항 누락, BOM/Part ID, 조립 순서, safety gate와 검증 공백을 조기에 드러내는 “living specification”이었다. 그러나 문서 제목과 README의 “설계 패키지 완료” 표현은 실제 성숙도보다 앞서 있다.

다음 정책을 적용한다.

- 기존 PDF는 `DRAFT / ARCHITECTURE SUBJECT TO CHANGE / NOT FOR FABRICATION` baseline으로만 보존한다.
- 2-tower architecture와 MVP scope가 잠길 때까지 최종 조립 순서·page count·발주 지침을 늘리지 않는다.
- Architecture Review → donor inventory → PDR → coupon/DFM → CDR → fabrication drawing release 이후에만 조립 PDF를 release candidate로 승격한다.
- 각 review에서 obsolete figure/part를 제거하고, 실제 MPN·공차·fastener·배선·검사 기준이 없는 페이지는 “미확정”으로 표시한다.

## 여과 없는 현재 blocker·애매점

1. **예산:** 기존 200,200 KRW safety relay 후보를 필수품처럼 계산한 비용표는 작업실 보유 안전장비 inventory 전에는 유효한 최소비용이 아니다. 다만 CNC·배송·세금·26개 미정 구매품도 남아 있어 200,000 KRW 목표가 닫혔다고 볼 수도 없다.
2. **수치는 잠겼지만 실물이 아님:** tower footprint/높이, stage/bin 범위, batch 용량과 cooling 길이는 계약에 잠겼다. 그러나 donor 질량·profile 길이·anchor substrate가 없어 상세 rack CAD와 joint/CG 물리 승인은 아직 열려 있다.
3. **IRLZ44N은 완성 heater driver가 아님:** 보유 MOSFET만으로 isolation, default-off, 방열, fuse coordination과 welded-on failure를 해결하지 못한다.
4. **Picamera2는 물리 BOM 명칭이 아님:** 실제 camera/lens/cable/lighting inventory가 없으면 두 optical system의 성능·비용을 확정할 수 없다.
5. **현재 CAD는 fabrication-ready가 아님:** 여러 STEP/DXF는 proof/RFQ precheck이며 최종 datum, GD&T, fit, material/heat treatment, surface finish와 fastener detail이 부족하다.
6. **구조 검토:** 1D beam FEA에서 reducer output과 unbraced tower column이 review-required였고, 새 rack은 전도·anchor·shelf joint·vibration 해석을 다시 해야 한다.
7. **검증 공백:** donor label/치수와 실제 물리시험 증거가 없다. RTX 3080 가상검증으로 하중·열·입자·진동 설계안을 먼저 좁힐 수 있지만, 그 결과를 실제 coupon 데이터로 잘못 표시하면 안 된다.
8. **TFT/센서 adapter 미선정:** UI state model은 있어도 실제 TFT controller/logic level, 온도·압력·전류·airflow front-end가 확정되지 않아 commissioning lock은 닫혀 있다.
9. **작업실 안전 inventory 부재:** 사용 가능한 safety relay/contactor, fused source, LOTO, guard와 thermal cutoff의 모델·정격이 아직 문서화되지 않아 신규구매가 필요한 범위를 판단할 수 없다.
10. **기존 이미지의 오해 위험:** proof envelope가 완성 기계처럼 보일 수 있다. 새 render가 나오기 전 기존 이미지는 concept/proof로만 표시해야 한다.
11. **원격 release:** GitHub 인증은 해결됐지만 remote 생성·push 후에도 물리 release tag를 만들 근거는 없다. 코드는 공유할 수 있어도 제작 승인 상태는 아니다.
12. **PCB proof는 생성됐으나 제작 HOLD:** `electronics/pcb/interface_board`에 네이티브 KiCad source, ERC/DRC 0, Gerber, SPICE/EMC/thermal 분석을 추가했다. 다만 keyed connector/passive MPN, harness/enclosure와 실제 전기·EMC 시험이 열려 있어 주문 승인본은 아니다.
13. **GPU solver 선정:** GPU는 확인됐지만 DEM/thermal/flow/structural 항목별 solver와 validation benchmark가 아직 잠기지 않았다. GPU 사용률만 높고 물리가 틀린 모델을 피해야 한다.

## 권장 다음 순서

1. [완료] 최소 end-to-end 요구, 2-tower 수치와 commissioning-only 범위를 `requirements/architecture_contract.md`에 잠근다.
2. IRLZ44N, camera/optics와 작업실 safety hardware를 사진·라벨·수량·정격으로 inventory한다.
3. Parent Codex가 private remote를 즉시 생성·push하고 이후 변경을 작은 revision 단위로 남긴다.
4. BOM의 `USER_STOCK/BUY/DNP` 분류와 비용 rollup을 재생성한다.
5. 두 tower skeleton, load path, access/guard/chute/cable layout을 만들고 RTX 3080 virtual validation으로 stage/bin/brace/cooling 후보를 줄인다.
6. [완료 — 제작 HOLD] architecture contract에 맞춘 최소 KiCad schematic과 단일-board 비교안을 작성해 CLI ERC, PCB DRC, SPICE/EMC/thermal review를 자동화한다.
7. concrete render review 후 살아남은 module detail만 단계적으로 이식한다.
8. 기존 PDF를 draft watermark 상태로 재빌드하고 최종 조립 문서 작업을 CDR 뒤로 미룬다.
