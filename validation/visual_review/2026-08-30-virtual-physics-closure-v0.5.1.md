# v0.5.1 멀티모달 CAD 검토 기록

- 날짜: 2026-08-30
- 검토자: parent Codex (실제 1600×1200 PNG 픽셀 직접 검토)
- revision: `virtual-physics-closure-v0.5.1`
- 렌더 재생성: `COMPACT_RENDER_GENERATION_OK images=29`
- 결과: **PASS_DIGITAL**
- 한계: 아래 판정은 강체 CAD와 렌더에 대한 가상 검증이다. 실제 배선 굽힘, 조립 공차, 변형 및 시운전 결과는 `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`이다.

## 검토한 실제 이미지

`compact_full_assembly_isometric.png`, `compact_full_assembly_top.png`, `compact_full_assembly_side.png`, `closed_operating_state.png`, `compact_exploded.png`, `compact_section.png`, `shredder_drive_guard_removed.png`, `heater_and_hot_zone.png`, `cooling_and_forming.png`, `forming_spool_motion.png`, `spool_and_dancer.png`, `cable_routing.png`, `service_access.png`를 원본 해상도로 확인했다.

## 필수 시각 검토 결과

| 항목 | 렌더 증거와 확인 내용 | 판정 |
|---|---|---|
| 운전 중 hopper 폐쇄 | `closed_operating_state.png`에서 입력 hopper의 PPR-C01 sliding lid가 rail 위 폐쇄 위치에 있고, 운전 상태에 guard·hot shield·control panel·duct가 모두 설치됨 | PASS |
| motor/chain guard | closed/isometric에서는 cutter chamber와 chain 구동부의 금속 guard가 설치됨. `shredder_drive_guard_removed.png`는 정비용 제거 상태를 별도 표시함 | PASS |
| band-heater 배선 여유 | `heater_and_hot_zone.png`의 shield 제거 검사 뷰에서 3개 band, T1–T3 probe, fuse와 상부 고정 duct 사이의 분리 경로가 보이며 열원과 lead가 중첩되지 않음 | PASS |
| cartridge lead strain relief | die heater lead가 terminal 쪽 keeper/duct 진입부로 빠지고 hot-zone 외부의 고정 duct로 연결됨 | PASS_DIGITAL |
| hot metal/PLA 분리 | closed 뷰에서 hot shield가 barrel/die를 둘러싸며, shield 제거 heater 뷰에서는 검사 목적상 열원과 printed-part 경계가 명확히 분리됨 | PASS |
| cooling route 연속성 | `cooling_and_forming.png`와 `forming_spool_motion.png`에서 die 이후 cooling tower → X/Y gauge → puller → solid-strand guide 순서가 끊기지 않음 | PASS |
| 불가능한 filament 굴곡 없음 | forming/spool 렌더의 guide–dancer–traverse–spool 경로가 직선/완만한 회전으로 이어지고 역꺾임이나 solid 관통이 없음 | PASS |
| full spool frame 여유 | isometric 및 spool 렌더의 1 kg full-spool envelope가 frame 내부에 있으며, full-motion 검사 결과 traverse 최소 25.0 mm 여유 | PASS |
| dancer 전 구간 | motion 렌더의 장착 위치와 guide 경로를 확인했고, 51개 강체 자세(-25°…+25°) 수치 검사에서 최소 여유 44.0 mm | PASS_DIGITAL |
| screw 정비 인출 | `service_access.png`에 screw-withdrawal keep-out과 hot-zone/control 분해 상태가 표시되고 PSU·panel·frame과 교차하지 않음 | PASS_DIGITAL |
| module bolt 공구 접근 | exploded/service-access 뷰에서 shredder, extruder, forming 및 spooler module의 분해 방향과 fastener 면이 frame member 뒤에 갇히지 않음 | PASS_DIGITAL |
| cable route 연속성 | `cable_routing.png`에서 hot-zone 수평 duct가 X/Y bridge를 거쳐 segregated vertical service duct까지 물리적으로 연속됨 | PASS |

## 검토 중 발견 및 수정

1. 최초 heater 검사 뷰에서는 hot shield가 heater/probe를 가려 검토성이 부족했다. 운전 상태에는 shield를 유지하고 heater 검사 뷰에서만 shield를 제거하도록 렌더 구성을 수정했다.
2. 최초 cable 뷰에서 hot-zone 수평 duct와 vertical service duct 사이에 실제 solid 연결이 없었다. `HeaterCableDuctBridgeX`, `HeaterCableDuctBridgeY` 금속 duct를 CAD source에 추가하고, 전체 충돌 검사를 다시 실행했다.
3. 수정 후 pairwise collision audit는 163 objects, 13,203 pairs, 의도된 interface 12, unexpected collision 0으로 PASS했다.

## 최종 판정

필수 11개 시각 확인 항목과 cable-route 보정 항목을 모두 만족한다. 이 결과는 `DIGITAL_FABRICATION_BASELINE`의 CAD 시각 증거이며 안전 인증이나 실물 조립/시운전 완료를 의미하지 않는다.
