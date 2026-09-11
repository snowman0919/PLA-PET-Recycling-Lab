# P9 빈 hot-zone 가열 검증

P9는 polymer를 투입하지 않은 상태에서 heater channel, T1-T5 mapping, dual one-shot thermal cutoff, 열팽창 여유를 확인한다. 모든 motor branch는 물리적으로 격리하고 grounded metal shield와 remote stop을 준비한다. P7/P8 stage release와 hot-zone receipt evidence가 검증되지 않으면 P9 기록 자체를 판정하지 않는다.

## 선행 검증

1. `analyze_p9_receipt.py templates/p9_hot_zone_receipt.csv`로 heater/probe/cutoff/TH-INS-01 수령 기록을 검증한다.
2. `validate_p7_stage_release.py`와 `validate_p8_stage_release.py`가 각각 유효한 P9 prerequisite를 반환해야 한다.
3. `validate_thermal_cutoff_topology.py`가 `TF-BARREL -> TF-DIE -> K0 coil`과 `TH-FUSE-01 = installed 2 + spare 1`을 확인해야 한다.
4. 별도 P9 heater-power 승인 기록은 이 bounded run에만 적용하며 지속 가열 권한이나 machine release가 아니다.

## 실행 기록

1. T1-T5를 independent reference logger와 대조하고 sensor open/short fault를 각각 검증한다.
2. PLA 180/195/205 C barrel + 200 C die, PET 245/260/270 C barrel + 265 C die를 기록한다. Mean +/- U95가 target +/-5 C 안에 있어야 한다.
3. 각 run의 peak + U95는 `generated_profiles.h`의 현재 firmware overtemperature ceiling보다 낮아야 한다.
4. Hot run 동안 sliding mount가 hard stop에 닿지 않아야 하며 cold available travel reference는 1.50 mm 이상이어야 한다.
5. `TF-BARREL`과 `TF-DIE`를 한 번에 하나씩 open-circuit 상태로 검증한다. 각각 독립적으로 K0/heater energy를 제거해야 한다.
6. SYS-04 die fastener는 M4x45 class 10.9 stock을 42.5 +/-0.1 mm로 절단/deburr하고 dry 1.50 N.m setting을 사용한다.
7. Cool-down 후 thermocouple retainer를 20 N으로 확인하고 이동량 <=0.10 mm, PE <=0.10 ohm, insulation >=1 Mohm @ 500 VDC를 재검사한다.

P9에서는 polymer leak-tightness를 판정하지 않는다. 누설은 P10 최초 PLA low-feed에서 평가한다. `analyze_p9_records.py`가 `P9_RECORD_CHECK_PASS`를 내더라도 `stage_p9_pass`, `p10_entry_prerequisite`, `material_feed_authorized`, `continuing_power_authority`는 모두 false다. P10 진입은 별도 human-reviewed P9 stage release가 필요하다.

## Stage release

`P9_RECORD_CHECK_PASS` 결과를 저장한 뒤 별도 검토자가 `templates/p9_stage_release.json`에 exact P7/P8 release, P9 receipt, thermal record, safety record, result SHA-256을 기록한다. `validate_p9_stage_release.py`는 현재 P9 analyzer로 전체 입력을 다시 계산한다.

`P9_STAGE_RELEASE_VALIDATED`만 P10 진입 검토에 사용할 수 있다. 이 상태에서도 `material_feed_authorized=false`, `continuing_power_authority=false`, `machine_release=HOLD`이며, 실제 PLA 투입에는 P10 전용 사용자 승인과 P10 evidence gate가 별도로 필요하다.

## TH-INS-01 열 차단 테이프

`TH-INS-01`은 안전장치가 아니라 grounded metal hot shield 외측의 보조 차열재다. heater band, barrel, die, TF-BARREL/TF-DIE, T1-T5/retainer, 전기 단자·커넥터, 통풍구 또는 moving envelope를 직접 덮지 않는다. P9 전에 `templates/s4_thermal_barrier_tape_smoke.csv`를 채우고 `analyze_s4_thermal_barrier_tape.py`가 `S4_THERMAL_BARRIER_TAPE_SMOKE_PASS`를 내야 한다. P9 receipt의 `tape_coupon_smoke_pass` evidence_path는 이 exact S4 result JSON을 가리켜야 하며 current tape contract SHA와 non-authorizing semantics를 다시 검증한다. backing은 polyimide film으로 기록하고, 접착제 화학종은 제공 정보에 없으면 `NOT_SPECIFIED_BY_LISTING`으로 명시한다. 현재 제품 정보의 장기 220–280 °C 중 하한 220 °C만 continuous design basis로 고정하며 단기 300 °C는 정상 운전 허용치로 사용하지 않는다.

최종 장착 상태에서는 현재 220 °C continuous design basis와 30 °C margin에 따라 가장 뜨거운 접착 interface의 `peak + U95 <=190 °C`가 반드시 성립해야 한다. 외측 표면 peak도 함께 기록해 실제 차열 효과를 비교하지만 이 값으로 hot-side limit을 완화하지 않는다. Cool-down 후 edge lift + U95 <=2.0 mm이며 smoke, char, melt, adhesive flow가 없어야 한다. 하나라도 실패하면 P9는 HOLD하고 tape 위치/재료 또는 shield 설계를 repository에서 수정한 뒤 S4/P9를 다시 수행한다.
