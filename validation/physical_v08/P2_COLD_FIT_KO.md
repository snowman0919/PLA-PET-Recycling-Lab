# P2 냉간 프레임·fit 검증

P2는 절삭/가열/재료 투입 전의 순수 기계 조립 gate다. P1에서 실제 재고와 수령 치수를 확인한 부품만 사용한다. 이 단계에서는 모터와 히터를 통전하지 않는다.

## 조립 순서

1. GGM 장착판 D02/D03의 drilling은 수령 packet에 대해 `analyze_ggm_mount_compatibility.py`가 `AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED`를 낸 뒤 별도 제작 승인을 받은 경우에만 현 도면을 사용한다. `HOLD_REDRAW_REQUIRED`이면 장공·확공·강제체결로 현장 보정하지 않는다.
2. 2020/2040 profile은 `profile_nesting.py` 결과와 실제 stock length를 대조한 뒤에만 절단한다. Frame base nominal은 470×700 mm다.
3. 기준면에 frame을 조립하고 700 mm 기준 rail squareness를 측정한다. 허용치는 0.50 mm/700 mm 이하이다.
4. CUT-03/CUT-05/CUT-05R/CUT-08/CUT-10과 bearing을 냉간 조립한다. 손회전 20회에서 rotating-to-static minimum clearance가 1.90 mm 이상이어야 한다.
5. Extruder rear datum/front sliding guide/retainer를 barrel dummy 또는 수령된 barrel 외경 기준으로 조립해 front guide의 사용 가능한 cold axial travel을 측정한다. 1.50 mm 이상이어야 한다.
6. Guard/cover를 임시 장착해 moving envelope 및 hot-zone envelope 침범이 없는지 확인한다. 간섭이 있으면 가드만 수정하고 구조 load path를 억지로 이동시키지 않는다.

## 기록

`templates/p2_cold_fit.csv`의 모든 행에 실측값, U95, 계측기 ID, 증거 경로를 기록한다. Boolean 항목도 사진/영상 또는 점검기록 경로가 필요하다. PASS는 `analyze_p2_records.py`로 계산하며 수기 PASS 문자열만으로 승격하지 않는다.
