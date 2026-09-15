# Chiron 기반 최소 제작 기준 — 2026-09-09

최신 사용자 자산을 policy.json에 고정했다. MCU만 고장 난 Anycubic Chiron 1대, 그 프린터에서 추출한 2020/2040 프로파일과 24 V 800 W PSU, M2~M6 나사, PLA 약10 kg와 ABS 약0.5 kg가 기준이다. 과거 Zortrax 또는 별도600 W PSU를 추가 자산으로 세지 않는다.

## 확정한 방향
사이클로이드에서 착안한 고토크 양축 분쇄 -> 공용 PLA/PET 압출 -> 냉각/직경 확인 -> 권취 구조를 유지한다. 프레임은2020 기본과 기존2040 국부보강을 그대로 사용한다. 별도 특수 spring 연구안을 본체 요구로 복원하지 않는다. 신규 CNC는 cutter/shaft/key/정밀 seat/screw-barrel-die 등 기능부에 집중한다. 평판과 가드는 절단·드릴·절곡, 저온 외장은 PLA 분할 출력, 고온·파편 장벽은 금속을 유지한다.

## 출력 재료와 전력
현재 print manifest의12종26개는 PLA712.33 g, ABS209.11 g다. ABS는 C05 냉각덕트, C06 gauge enclosure, C07 puller guard에 배정한다. ABS100 g 예비분까지 합쳐309.11 g이므로 현재500 g 내에 들어간다. 새 전체 외장 패널은 이 수량에 아직 포함되지 않으며 PLA로 배정한다.
resource_budget.py는 기존36개 STL/3MF/STEP 해시를 대조한다. 새로 slice하거나 실제 출력했다고 주장하지 않는다. 기존 부품 재질이 목표와 일치하므로 라벨만 바꿔 새 검증을 만들지 않는다.
800 W는 사용자 보고값이다. 24 V 출력이라면 정격전류33.33 A지만, 실제 모델/라벨과 DC OUTPUT을 확인해야 한다. 기존 model의600 W와500 W 운전 cap은 검증 이력으로 보존하며, 새 자산값으로 출력 명령이나 배선/fuse를 자동 상향하지 않는다. 압출 모드490 W, 분쇄 모드477 W를 동시에 합산해 운전하지 않는다.

## 새 PTC
220 VAC,245 C급 PTC는 보유 예비품이다. W·치수·절연·온도 정의가 없고 기존PET 설정265~270 C의 주가열원을 대체한다는 근거가 없다. 공용MVP에는 기존24 V 제어 가열기를 유지한다. PTC를24 V MOSFET에 연결하거나800 W DC 예산에 더하지 않는다. 공짜 소자 때문에 별도AC 스위칭/차폐 부품을 추가하지 않는다.

## 도너 적용과 확정 전 확인
Chiron 기구·모터·센서·팬은 우선 재사용한다. 다만 현재 puller/spooler 어댑터는PWM/DIR이고 stepper는STEP/DIR이라 인터페이스를 확인한 뒤 해당 어댑터만 변경한다. Z축 나사와 선형부는 실제 치수로 traverse에 배정한다. donor heater 치수/전압/출력, NTC와Type-K 구분은 유지한다. 모든 소형 부품에 고가 시험을 요구하지 않는다.
필요 재고는 sourcing/minimum_confirmation_bom.csv에서 모아 확인한다. 구매수량은 보유량 답변 전까지 미확정이며, 이미 확보한PSU/프로파일/필라멘트/나사/소형구동품을 다시 구매하지 않는다.

## 검증과 상태
python3 bom/practical_mvp/build_plan.py
python3 bom/practical_mvp/resource_budget.py
python3 bom/practical_mvp/test_plan.py
python3 bom/practical_mvp/test_resources.py

기준선은 확정했지만 donor 접합 치수, 기존 rear hot-mount 수정과 공차, 실제 출력/통전은 별도다. 현재 machine_release=HOLD, physical_validation=NOT_RUN이다. 과거FABRICATION ZIP을 최신 완성본으로 배포하지 않는다.

## 모터·전자부품 최신 회신

BTS7960·Arduino Mega·E-stop은 사용자 보유 회신으로 반영했다. 히터는 구매 대상이다. 모터는 사진의24V120RPM/24V57RPM 후보와 같은브랜드 공개정격표를 구분해 검토했다. 최신 재고 질문과 계산은 `motor_selection_20260909/remaining_confirmation_bom.csv`, `REVIEW_KO.md`, `result.json`을 따른다. 회신전 sourcing/minimum_confirmation_bom.csv의 미확인 상태를 최신 재고로 재사용하지 않는다.

## 수량 확정 추가

모터 두 개는 구매 전 옵션이다. BTS7960은2개 보유로 확인되어 분쇄기/압출기에1개씩 계획 배정하고 추가 구매량은0이다. 미식별24V DC2채널 컨트롤러2개는 예비로 등록했다. 정격전류·정역회전·MCU 입력 방식이 확인되기 전에는 구동회로에 자동 배정하지 않는다. 최신 재고표는 `motor_selection_20260909/update_stock_view.py`로 재생성한다.

## 시퀀스 기반 모터 기준 선정
최신 모터 기준은 `analysis/motor_sizing_v08/README_KO.md` 및 `motor_selection.json`이다. GGM24V60W/75:1+기존chain2.5 분쇄,같은모터150:1직결 압출을 선택했다. 미식별DC보드는MVP에서제외하며BTS7960두개를유지한다. 구매/보호한도교정/어댑터CAD/실물가동은별도이며 과거22N.m trip을새감속기에그대로쓰지않는다.
