# 교정 절차

상태: 설계 패키지 절차. 실제 계측기 ID·교정일·원시값 없이 `PASS`로 기록하지 않는다.

## 공통 기록

모든 교정 CSV에 날짜/작업자, 장치 revision/commit, 환경온도·습도, 계측기 모델·serial·교정만료, 원료 lot, 반복횟수, 원시값, 계산값과 합격/실패를 남긴다. 실패값을 삭제하지 않고 수정 전후 run ID를 분리한다.

## 1. FDM tolerance coupon

1. `exports/stl/tolerance_coupon.stl`을 source orientation, slicer compensation 0으로 출력한다.
2. printer, nozzle, layer height, wall count, material·lot와 실제 bed 위치를 기록한다.
3. Base/comb가 융합되지 않았는지 확인하고 0.10–0.50 mm slot에 10 mm tab을 넣어 `불가/압입/위치결정/slide/과유격`을 기록한다.
4. 3.8–4.6 mm holes을 0.01 mm caliper 또는 pin gauge로 X/Y 각각 3회 측정한다.
5. Bearing·heat-set insert는 실제 공급품별 별도 coupon으로 push force, crack와 pull-out을 시험한다.

현재 baseline locating 0.10 mm, general slide 0.25 mm, flake-exposed slide 0.40 mm는 물리 coupon 전 provisional이다. Cutter/blade clearance와 bearing preload는 이 결과가 아니라 metal shim/가공 공차로 정한다.

## 2. 직경 게이지

필요 장비는 인증값이 있는 1.50/1.75/2.00/2.50 mm pin, rigid fixture, 고정 camera exposure/white balance/focus, 두 backlight, 온도계와 오염 coupon이다.

1. 보호창과 front-surface mirror를 승인 방법으로 세정하고 warm-up 15 min 후 camera setting을 잠근다.
2. 각 pin을 X/Y field의 중앙·네 모서리에 놓고 각 위치 30 frame을 수집한다.
3. 두 view를 독립으로 radial-distortion 역보정하고 3×3 homography, threshold와 mm/pixel scale을 fit한다.
4. Pin 인증불확도, 위치 반복성, threshold, focus/온도 drift와 residual을 합성해 U95를 계산한다.
5. Clear/black/translucent filament, 보호창 먼지, stray light와 vibration을 주입해 contamination detector와 dropout을 시험한다.
6. `d_avg=(dx+dy)/2`, `ovality=|dx-dy|`가 동일 frame ID로 10 Hz 저장되는지 확인한다.

합격 기준은 전 field bias ≤0.010 mm, `U95≤0.020 mm`, 처리율 10 Hz, 3 s dropout에서 PAUSE다. 실패하면 software로 공차를 숨기지 않고 optic/working distance/light/focus를 변경한다.

## 3. 온도·압력·airflow

- Extruder 4개와 dryer control sensor를 traceable dry-block/temperature reference에서 최소 25/100/180/230/280 °C로 비교한다. Sensor 종류 정격을 넘는 점은 사용하지 않는다.
- Open/short/ADC rail을 하나씩 주입해 firmware가 plausible temperature가 아닌 fault로 판정하는지 확인한다.
- Melt pressure transducer는 qualified pressure calibrator와 zero/25/50/75/100% span을 상승·하강 반복한다. 3/5/6.5/8 MPa alarm map과 독립 D27 trip을 분리 기록한다.
- Strand 위치 3개 덕트×9점에서 2.5/4.0 m/s velocity map을 만들고 D28 discrete airflow proof의 on/off point와 hysteresis를 측정한다.

합격 전 `firmware/arduino_mega/src/configuration.h`의 qualification flag는 `false`로 유지한다. 계수·fault 결과와 reviewer 서명이 있는 commit에서만 하나씩 연다.

## 4. Current·encoder·jam

Shredder/extruder/forming current conditioner를 0–예상 peak 범위의 calibrated load와 비교하고 offset, gain, RMS/peak bandwidth를 기록한다. 각 encoder는 traceable tachometer/길이 기준으로 counts/rev, direction, missed count를 1/최대속도에서 검증한다.

Jam coupon은 current RMS·peak·derivative와 speed drop을 동시에 기록한다. 250 ms feed-limit, 추가 500 ms stop, 300 ms dwell, 800 ms reverse, 3회 뒤 7.372 s 이내 latched fault를 확인한다. 실제 cutter 없이 electronic/low-energy rig부터 시작한다.

## 5. Puller·dancer·traverse

- Puller Ø40 mm roller의 encoder 길이를 10 m traceable filament/wire에 비교해 speed error ≤1%를 확인한다.
- Ø30 mm odometer와 drive encoder slip은 정상 ≤2%, 3%/1 s warning, 5% stop으로 교정한다.
- Dancer −30/−15/0/+15/+30°를 dead-weight로 상승·하강 10회 측정해 0.5±0.1 N과 hysteresis를 확인한다.
- Traverse home/end, 70 mm travel과 core/full speed 8.00/3.20 mm/min을 검증한다.

상세 합격 기준과 장시간 coupon은 `validation/test_plans/forming_line_coupon.md`와 `spooler_coupon.md`를 따른다.
