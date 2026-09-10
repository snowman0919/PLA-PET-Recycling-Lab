# P2 냉간 프레임·fit 검증

P2는 절삭/가열/재료 투입 전의 순수 기계 조립 gate다. P1에서 실제 재고와 수령 치수를 확인한 부품만 사용한다. 이 단계에서는 모터와 히터를 통전하지 않는다.

## 조립 순서

1. GGM 장착판 D02/D03의 drilling은 수령 packet에 대해 `analyze_ggm_mount_compatibility.py`가 `AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED`를 낸 뒤 별도 제작 승인을 받은 경우에만 현 도면을 사용한다. `HOLD_REDRAW_REQUIRED`이면 장공·확공·강제체결로 현장 보정하지 않는다.
2. 2020/2040 profile은 evidence hash가 검증된 stock record와 `profile_nesting.py` 결과를 대조한 뒤에만 절단한다. Solver는 실측 usable length에서 U95를 차감한 보수적 길이와 지정한 per-cut kerf budget으로 배치한다. Frame base nominal은 470×700 mm다.
3. 기준면에 frame을 조립한다. FR-001의 일반공차 ISO 2768-m에 따라 base X=470±0.8 mm, Y=700±0.8 mm를 적용하며 각 치수는 `측정값±U95` 전체가 범위 안에 있어야 한다. 두 대각선은 각각 독립 측정하고 `|A-B| + U95_A + U95_B <= 1.0 mm`를 만족해야 하며 네 모서리 rocking이 없어야 한다. 700 mm 기준 rail squareness도 U95 포함 0.50 mm 이하이다.
4. CUT-03/CUT-05/CUT-05R/CUT-08/CUT-10과 bearing을 냉간 조립한다. 손회전 20회에서 rotating-to-static minimum clearance가 1.90 mm 이상이어야 한다.
5. Extruder rear datum/front sliding guide/retainer를 barrel dummy 또는 수령된 barrel 외경 기준으로 조립해 front guide의 사용 가능한 cold axial travel을 측정한다. 1.50 mm 이상이어야 한다.
6. Guard/cover를 임시 장착해 moving envelope 및 hot-zone envelope 침범이 없는지 확인한다. 간섭이 있으면 가드만 수정하고 구조 load path를 억지로 이동시키지 않는다.

## 기록

`templates/p2_cold_fit.csv`의 모든 numeric 행에 실측값, U95, 단위, 계측기 ID·교정 참조, 작업자·검토자, ISO timestamp, 저장소 상대 evidence 경로와 SHA-256을 기록한다. Boolean 항목도 작업자·검토자·timestamp와 사진/영상 또는 점검기록의 경로/hash가 필요하다. `analyze_p2_records.py`는 evidence hash와 단위를 먼저 검증하고 공차 경계에서 불확도를 보수적으로 반영한다. 출력의 `fabrication_authorized`와 `stage_release_granted`는 항상 false이며, 계산 PASS만으로 다음 물리행동이 승인되지 않는다.
