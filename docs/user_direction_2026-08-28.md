# 사용자 방향성 변경 요청 — 2026-08-28

상태: **architecture re-scope input / parent Codex decision required**  
적용 대상: 다음 아키텍처 revision, BOM 조달 분류, CAD·render 전략, 문서 release 정책

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

현재 알려진 공개 가격 floor 235,200 KRW에서 Camera Module 3 후보 35,000 KRW를 제외해도 safety relay 후보만 200,200 KRW이므로, 200,000 KRW 전체 신규 구매 목표는 배송·세금·나머지 26개 BUY/CNC를 넣기 전 이미 사실상 초과한다. 안전 relay를 값싼 일반 relay로 바꿔 예산을 맞추지 않는다. 실제 project-lab safety stock 또는 예산 재협의가 필요하다.

## 3. 원격 저장소

사용자는 GitHub CLI login을 완료했다. 현재 local repository에는 remote가 없다. 프로젝트 규칙상 외부 저장소 생성·remote 설정·초기 push는 parent Codex가 소유한다.

권장 기본값:

- repository: `snowman0919/PPR`
- visibility: `private`
- remote: `origin`
- 초기 push 전 확인: `.env`/token/cache/order temp 부재, licensing 범위, clean worktree, 전체 validation PASS

Parent Codex는 동일 이름 저장소 부재와 인증 성공을 확인한 뒤 저장소를 생성하고 main을 push한다. 공개 전환은 hardware/CAD license, 안전 면책, third-party asset을 별도 review한 뒤 수행한다.

## 4. CAD/render 구체화 요구

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

## 5. 설계·조립 문서의 현재 위치

사용자의 지적이 맞다. 현재 architecture, donor, 상세 가공도와 물리 coupon이 열려 있는데 `제작·조립 매뉴얼`을 완성본처럼 제시한 것은 시기상조다.

기존 PDF를 만든 합리적 목적은 요구사항 누락, BOM/Part ID, 조립 순서, safety gate와 검증 공백을 조기에 드러내는 “living specification”이었다. 그러나 문서 제목과 README의 “설계 패키지 완료” 표현은 실제 성숙도보다 앞서 있다.

다음 정책을 적용한다.

- 기존 PDF는 `DRAFT / ARCHITECTURE SUBJECT TO CHANGE / NOT FOR FABRICATION` baseline으로만 보존한다.
- 2-tower architecture와 MVP scope가 잠길 때까지 최종 조립 순서·page count·발주 지침을 늘리지 않는다.
- Architecture Review → donor inventory → PDR → coupon/DFM → CDR → fabrication drawing release 이후에만 조립 PDF를 release candidate로 승격한다.
- 각 review에서 obsolete figure/part를 제거하고, 실제 MPN·공차·fastener·배선·검사 기준이 없는 페이지는 “미확정”으로 표시한다.

## 여과 없는 현재 blocker·애매점

1. **예산:** camera 보유를 인정해도 공개 safety relay 후보 하나가 200,200 KRW이며 CNC·배송·세금·26개 미정 구매품이 남아 있다. 현재 200,000 KRW 목표는 증거상 닫히지 않는다.
2. **규모 축소가 아직 수치가 아님:** “조금 줄인다”만으로는 CAD를 바꿀 수 없다. tower footprint/높이, stage 수, bin 수, batch 용량과 cooling 길이를 숫자로 잠가야 한다.
3. **IRLZ44N은 완성 heater driver가 아님:** 보유 MOSFET만으로 isolation, default-off, 방열, fuse coordination과 welded-on failure를 해결하지 못한다.
4. **Picamera2는 물리 BOM 명칭이 아님:** 실제 camera/lens/cable/lighting inventory가 없으면 두 optical system의 성능·비용을 확정할 수 없다.
5. **현재 CAD는 fabrication-ready가 아님:** 여러 STEP/DXF는 proof/RFQ precheck이며 최종 datum, GD&T, fit, material/heat treatment, surface finish와 fastener detail이 부족하다.
6. **구조 검토:** 1D beam FEA에서 reducer output과 unbraced tower column이 review-required였고, 새 rack은 전도·anchor·shelf joint·vibration 해석을 다시 해야 한다.
7. **물리 검증 전무:** donor label/치수, cutter torque, bearing fit, dryer moisture, melt pressure, gauge U95, classifier confusion matrix, 30분 처리량/직경과 1 kg winding 증거가 없다.
8. **TFT/센서 adapter 미선정:** UI state model은 있어도 실제 TFT controller/logic level, 온도·압력·전류·airflow front-end가 확정되지 않아 commissioning lock은 닫혀 있다.
9. **안전 부품과 전원:** PSU label, wire/fuse rating, safety relay/contactor, heater thermal limit와 PE/grounded enclosure가 실물 기준으로 선정되지 않았다.
10. **기존 이미지의 오해 위험:** proof envelope가 완성 기계처럼 보일 수 있다. 새 render가 나오기 전 기존 이미지는 concept/proof로만 표시해야 한다.
11. **원격 release:** GitHub 인증은 해결됐지만 remote 생성·push 후에도 물리 release tag를 만들 근거는 없다. 코드는 공유할 수 있어도 제작 승인 상태는 아니다.

## 권장 다음 순서

1. 사용자와 2-tower 수치·MVP 범위를 한 페이지 architecture contract로 잠근다.
2. IRLZ44N과 camera/optics를 포함한 user stock inventory를 사진·라벨·수량으로 작성한다.
3. BOM의 구매/보유 분류와 비용 rollup을 재생성한다.
4. 두 tower skeleton, load path, access/guard/chute/cable layout만 먼저 CAD로 만든다.
5. concrete render review 후 각 module detail을 단계적으로 이식한다.
6. 기존 PDF를 draft watermark 상태로 재빌드하고 최종 조립 문서 작업을 CDR 뒤로 미룬다.
7. Parent Codex가 private remote를 생성·push하되 release status는 `ARCHITECTURE RESCOPE / PHYSICAL RELEASE NOT READY`로 유지한다.
