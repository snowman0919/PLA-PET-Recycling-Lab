# PLA/PET Recycling Lab v1.0.0-rc1 제작 후보

이 자산은 `final-design-fabrication-closure-v0.8`의 디지털 설계·해석·제작 문서 후보이며 물리 시험 또는 안전 인증 결과가 아니다.

- release tag: `v1.0.0-rc1` (게시하지 않음)
- release state: `IN_PROGRESS` — 제작 후보 승인 전
- design state: `REOPENED_FOR_VALIDATION`
- validation basis: `OPENMODELICA_CALCULIX_CLOSED_FORM_CAD`
- cross-solver state: `NOT_COMPLETED_BY_SCOPE_DECISION`
- physical validation state: `NOT_RUN`
- safety certification: `NOT_CERTIFIED`
- procurement gate: `USER_APPROVAL_REQUIRED`
- commissioning gate: `USER_APPROVAL_REQUIRED`
- fabrication release approval: `USER_APPROVAL_REQUIRED`

기존 `dist/PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION.zip`은 이번 재감사 결과를 포함하지 않는 과거 산출물이다. 현재 제작·구매 기준으로 사용하지 않는다. 최신 상태는 `validation/results/v08_full_compliance.json` 및 `analysis/final_validation/results/v0.8/loaded_phase.json`을 따른다. hot-zone 재료·국부응력·접합부, 하중 위상, 공차/체결부 HOLD가 해소되고 패키지 재검증이 끝나야 새 제작 후보를 선언한다.

구매 승인 전에는 대상 MPN·정격·요구 치수·가격·대체 조건을 검토한다. Donor 라벨·전압·전류·토크·축경·센서 형식은 증거로 확정하며 추측하지 않는다. 수령 후에는 치수와 정격을 확인하고, 조립 후에는 실제 fit과 냉간 clearance를 검사한다. 열간 clearance와 interlock/PE/fuse 기능 시험은 해당 통전·시운전 단계의 선행 조건과 별도 사용자 승인 아래 수행한다. 각 결과는 해당 후속 단계의 승인 증거로 사용한다. 구매·가공·통전의 별도 승인과 단계별 물리 gate는 유지한다.

전체 검증의 최신 항목별 판정은 `validation/results/v08_full_compliance.json`을 따른다. 현재 전체 상태는 `FAIL`이다. `release_readiness_ko.md`의 13항목 산출물 감사와 전체 25항목 compliance는 서로 다른 검사 범위다. 과거 `release_approval_report_ko.md`의 PASS와 동결 선언은 현재 승인 근거가 아니다.

ZIP 검증기는 내부 해시뿐 아니라 manifest가 가리키는 현재 작업트리 원본의 크기와
SHA-256도 대조한다. 같은 Git commit에서 수정한 원본도 과거 패키지와 구분한다.
재검사에서 기존 ZIP의 `exports/print/PPR-C01/dimension_sheet.svg`가 현재 원본과
달라 거부됐다. 같은 크기의 내용 변경을 거부하는 회귀 시험도 통과했다.
모든 디지털 gate가 닫힌 뒤 현재 원본으로 패키지를 재생성·재검증해야 한다.

생성 단계는 inventory13항목 및 compliance25항목의 정확한 항목 집합과 v0.8
리비전을 요구한다. 생성 후 검사할 패키지 항목만 선행조건에서 제외하며, 나머지는
모두 명시적으로 통과해야 한다. 빈 결과, 누락 항목, 문자열 False, HOLD, 과거
리비전을 거부하는 부정 시험5개를 실행했다. 최신 inventory는12/13 IN_PROGRESS다.

이 단계에서는 GitHub Release를 만들거나 게시하지 않는다. branch와 PR은 디지털 변경 검토용이며 merge도 자동 수행하지 않는다.

# JLCCNC 공급 능력 회신

2026-09-08 수신한 JLCCNC 서면 회신은 비목록 SCM440 조달, Q&T 및 가스질화를
지원하지 않고 일반 최저 치수 공차를 ±0.05 mm로 안내했다. 동일 heat/process
coupon을 먼저 승인한 뒤 같은 주문의 본품을 진행하는 순서도 지원하지 않는다.
따라서 JLCCNC는 현 `EX-SCR-01`/`EX-BAR-01` 사양의 일괄 공급처에서 제외한다.
전문 SCM440/Q&T/질화/후가공 업체 선정 전 hot-zone과 발주 HOLD를 유지한다.
판정 근거와 원본 EML SHA-256은 `jlccnc_response_2026-09-08_ko.md`에 있다.

# 공차 인터페이스 갱신

CUT-02는 단순 공차 적층품이 아니라 위치 식별된 matched-ground set으로 공급하고,
금속 shim 적용 후 11개 축방향 간극 전부를 전 회전 검사하도록 변경했다. IF-032
판재/출력 슬롯은 0.05–0.75 mm로 배분했다. SKF 공식 Normal/ISO 492 한계와 현재
Ø25 h6/Ø42 H7 도면을 결합해 61905 내·외륜 fit 및 cutter/hub/phase-key fit을 계산했다.
추가 폐쇄에서 T1–T3 sensor bore를 flat-bottom Ø3.20 +0.05/0,
깊이5.40±0.05로 변경해 보수적 ligament3.345 mm(요구≥3.32)를 확보했다.
릴리스 형상을 사용한 4단계 3D 열–압력 국부해석도 medium→fine 변화1.635%,
조건부 응력49.935 MPa로 수렴해 형상/국부응력 항목은 PASS로 분리했다. 다만
245–270°C SCM440 허용강도는 공급자 근거가 없어 별도 HOLD다.
SYS-04의 이전 M4×40/torque-HOLD 선택은 SUPERSEDED다. 현행은 M4×45
class10.9 stock screw를 42.5±0.1 mm로 절단·디버링하고 dry1.50 N·m로 체결한다.
다이 grip34.95–35.05 mm와 압축 gasket0.25–0.53 mm에서 물림6.82–7.40 mm,
완전 나사8.00 mm 기준 thread-bottom 여유0.60–1.18 mm다. 6 MPa digital
load-path qualification은 PASS이며 실제 수령·누설·첫 thermal cycle은 NOT_RUN이다.
배럴–다이는 2×Ø3 H7/m6 dowel과 true-position stack으로 축 offset≤0.024 mm를
배분했고, shredder axial float와 X/Y gauge는 완성 조립 기능검사로 고정했다.
SKF 625/6001 Normal 공차를 축 h6 도면과 결합해 IF-010/IF-016를 닫았다.
조립되지 않던 FD-TRN-01은 폐기하고 FD-HOP-01–FD-MET-01을 등록 spigot/socket과
flow-path 외측 FD-GSK-01로 직접 연결했다. FreeCAD 명목 간섭0, 등록 반경
여유0.050 mm이고 IF-031의 flow-path 확장0–0.15 mm와 등록 diametral
clearance0.10–0.16 mm를 닫았다. Gasket 압축·누설·잔류 물리검사는 NOT_RUN이다.
최신 공차표는 48개 중 40 PASS/8 HOLD이며 모든 실물 fit은 `NOT_RUN`이다. TS-07/IF-023은 band free-state ID34.10–34.20 mm와 usable closure≥1.00 mm를 적용해 최악 closure reserve0.277 mm로 디지털 PASS했으며, 8-sector 접촉 검사는 실물 수령 전 `NOT_RUN`이다. IF-017은 실제로 판 밖에 있던 6001 베어링을 10 mm SP-BP-01의 Ø28 H7×8.05–8.10 pocket 안으로 옮기고, integral shoulder와 SP-BR-01 금속 retainer로 0.05–0.22 mm axial clearance 및 0.9455–1.000 mm outer-ring overlap을 확보해 디지털 PASS했다. IF-011은 FM-GR-01에 매입형 FM-GC-01 금속 캡 2개와 3개 균형 관통 체결을 추가해 23–60 °C POM-C/베어링강 차등팽창에서 계산 clearance0–0.096 mm, axial clearance0.10–0.22 mm, outer-ring overlap0.446–0.500 mm를 확보했다. IF-028은 PPR-C06/C11의 방향이 맞지 않는 blind heat-set insert를 Ø3.40–3.50 관통공과 washer/all-metal nut로 교체해 M3 diametral clearance0.40–0.50 mm 및 내부 공구 접근을 확보했다. Blue-check·열간 TIR·자유회전·축방향 고정과 모든 실물 체결 검사는 `NOT_RUN`이다. IF-029의 잘못된/선택식 M4 heat-set insert 경로는 제거하고 PPR-C01의 flush countersunk through-bolt와 PPR-C10의 through-bolt를 각각 washer/nyloc으로 단일화했다. IF-024는 Tempco custom Hi-Density Ø6.500±0.013 Type CG×39.50±0.20, HTL lead와 MFR 금속 flange를 지정하고 EX-DIE-01을 Ø6.55 H7 관통공과 2×M3 flange 체결로 변경했다. 계산 diametral clearance0.037–0.078 mm와 SYS-16 양의 고정으로 디지털 PASS했지만 제조사 승인도면·견적·수령검사·통전은 HOLD다. IF-030은 `fastener_schedule.csv`의 고유 joint 29개가 모든 계약 필드를 가지며 생성된 조립 단계에서 1:1 참조됨을 검사해 디지털 coverage PASS했다. SYS-04/12의 물리 HOLD는 별도 유지한다.

정정(현재 source 기준): 위 40 PASS/8 HOLD 및 joint29 표기는 이전 생성 상태다.
IF-025/026은 Tempco MTA1 맞춤 K/U/Q 프로브(Ø3.00±0.03 mm, Alloy600,
공급자 용접 stop collar), 배럴 삽입5.20±0.05 mm, 다이 삽입10.00±0.05 mm,
TH-TCR-01 bridge와 SYS-17 체결 계약으로 디지털 PASS했다. 계산 diametral
clearance는0.17–0.28 mm, 배럴 선단 간극0.10–0.30 mm, 다이 bottom gap은
1.90–2.10 mm다. 승인도면·견적·수령 치수·절연·교정·열응답·pull 시험은
HOLD/NOT_RUN이다. T1 간섭은 EX-MT-02를 X270에서 X265 mm로 이동해 제거했다.
IF-020은 NSK 51102와 Ø15 h6×11 seat, Ø23.00–23.05 integral abutment,
Ø28.30–28.35×9.10–9.15 pocket 및0.05–0.30 mm 금속 shim 계약으로
디지털 PASS했다. 6 MPa/Ø16.22 mm 막힘 조건의 추력은1,239.8 N이고
dynamic/static rating SF는8.55/13.55다. 수령 치수·blue-check·endplay·추력
proof는 NOT_RUN이다. IF-008은 TT Motor GMP60-60127-2460 공개 도면 nominal에
수령 합격범위를 붙이고 DRV-A60 pilot bore와 DRV-F01A D-bore 제작 한계를 수치화해
디지털 기준 변형으로 닫았다. 다른 donor는 새 Axx/F01Axx 편차와 재검증이 필요하며,
구매·수령·Gate-1은 HOLD/NOT_RUN이다. IF-022는 StepperOnline 17E1K-07,
EG17-G10, CL42T-V41을 디지털 기준 구동계로 고정하고 FD-DA-01 금속 mount와
FD-CP-01 keyed/cross-pinned coupling, D44 STEP/D42 DIR/D46 ENA/D47 ALM을
CAD·BOM·firmware에 일치시켜 PASS했다. 연속 gearbox 정격5 N·m 대비 설계
토크2.2 N·m의 정격비는2.273이며, 구매·수령 치수와 저속 torque-arm 시험은
HOLD/NOT_RUN이다. 따라서 최신 공차표는 48개 중46 PASS/2 HOLD,
IF-030 joint는30개다.

IF-027을 만들던 호퍼 유지용 PTC·spreader·clamp와 전용 출력은 활성 설계에서
제거했다. 동결 아키텍처는 `external predry`를 요구하고 호퍼 PTC를 요구하지 않으며,
이 미선정 보조 가열기는 PET 건조를 대체하지도 못했다. 따라서 CAD·BOM·thermal
channel·I/O·firmware에서 단일 제거하고 IF-027은 `REMOVED_FROM_ACTIVE_ARCHITECTURE`
로 닫는다. T5는 밀폐 feed hopper 감시용 비가열 센서로 유지한다.

Graphify 코드 AST 증분은 17,594 nodes/35,913 edges/1,289 communities로 갱신했다. 변경 문서·도면의
semantic 증분은 승인된 유료 backend가 없어 미완료이며, 현재 커밋 조건을 충족한
것으로 간주하지 않는다.
# 펌웨어 소스 증적 재감사

원본 및 출시 소스의 manifest SHA-256, 누락 파일, 추가 컴파일 입력과 HEX를
공통 검사로 대조한다. 전체 compliance, inventory 및 ZIP builder에 적용했다.
원본 변경·출시본 변경·미등록 CPP 추가의 3개 음성 시험을 통과했다.
출시 재빌드 스크립트는 CLI·core·compiler 버전 및 library lock을 대조하고
빈 임시 `--build-path`와 `--clean`을 사용하도록 수정했다. 실제 실행에서
기존 출시 HEX SHA-256 `e4f67a278ff204cd681cf70357047294478478ce365fa3838dc8be6e858274ae`와
일치했다. CLI 1.5.1은 flake.lock의 nixpkgs 고정 revision에서 복구했다.
이 결과는 제작 승인이나 물리 검증을 뜻하지 않는다.


## 2026-09-09 직접 하중 경로 및 열간 접합 재검토

오른쪽 CUT-05R의 기존 공통 키홈이 베어링 좌면을 가로지르는 형상 오류를 수정했다.
오른쪽 cutter keyseat는 local Y85–165 mm, phase keyseat는 Y212–240 mm이며,
좌면 Y57–69/Y197–209 mm에는 키홈이 없다. 좌·우 shaft variant를 조립체·제조 지그·clocking 검사에 명시했다.

수정된 실제 keyed STEP으로 18개 C3D4 하중 사례를 실행했고, 지정 resultant의 평형과 변위 수렴을 확인했다.
22 N·m fuse 사례, slack60 N, hook 반경18 mm는 조건부 입력이며 추가 wedge 법선력·키/베어링 접촉·피로는 미완료다.
고온부 실제 BRep의 자유팽창 48개 부품쌍 상태 중14개에서 간섭이 나타났으므로 무조건적인 sliding 가정을 허용하지 않는다.
정상 운전 온도장·접촉과 고온 재료·die 잔류 예압이 닫히기 전 전체 제작 상태는 HOLD다.

현재 수정본의 검토 STEP·키홈 변경도·PDF·수치 증거는 `exports/review/engineering-closure-20260909/`와
`dist/PPR-v08-engineering-review-20260909.zip`에 모았다. 이것은 최종 FABRICATION ZIP이 아니며,
`component_review_BOM.csv`도 변경 축2종만 포함한다. 기존 `exports/final/`와 과거 FABRICATION ZIP을
이번 변경이 모두 반영된 제작 기준으로 간주하지 않는다. 도면·공차표·검증의 영향 범위 재생성 후에만 승격한다.

직접 수정·실행 근거: `docs/reviews/design-load-closure-20260909/` 및 그 안의 `final_check.json`.
Chromium PDF 도구는 sandbox 설정 오류로 실행되지 않았으며 보안정책을 변경하지 않았다.
기존 Typst0.15.1로 3쪽 PDF를 생성하고 Poppler 렌더3쪽을 직접 검토했다.
