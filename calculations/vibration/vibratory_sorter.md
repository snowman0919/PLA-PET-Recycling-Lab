# 진동 이송·3방향 선별 proof 계산

- 상태: 해석·CAD 후보, 물리 진동/입도 시험 미검증
- 경로: `>6 mm/긴 strip → Stage 3 재순환`, `3–6 mm → dryer/storage`, `<3 mm → 밀폐 fines bin`
- 기준 처리량: 명목 250 g/h, 연속 안정 목표 200 g/h

## 구조

304×128 mm 탈착식 2단 screen cassette를 8° 하향 배치한다. 상단 6.0 mm square aperture는 oversize를 보류하고, 하단 3.0 mm aperture는 acceptable flake를 보류하며 fines를 통과시킨다. cassette는 M5 screw clamp로 고정하고 snap fit을 쓰지 않는다. 실제 woven/perforated mesh의 명목·실측 aperture와 긴 PET strip의 자세 효과는 coupon으로 결정한다.

| 항목 | 기준값 | 의미 |
|---|---:|---|
| moving mass | 1.5 kg | tray, screens, material, drive bracket 포함 가정 |
| eccentric mass/radius | 40 g / 12 mm | 480 g·mm unbalance |
| 운전점 | 1800 rpm = 30 Hz | donor DC/BLDC baseline; NEMA17은 대안 시험품 |
| isolator natural frequency | 8 Hz | 4개 합성 stiffness 3.79 kN/m |
| damping ratio | 0.15 | 고무 후보의 선형 등가값 |
| tray slope | 8° | 중력 이송 보조 |

## 강제진동

편심력과 1자유도 응답은 다음을 사용한다.

$$F_0=m_e r\omega^2$$

$$X=\frac{F_0}{\sqrt{(k-m\omega^2)^2+(c\omega)^2}}$$

30 Hz에서 편심력 peak는 `17.05 N`, tray 진폭은 `0.344 mm peak`, 가속도는 `1.24 g peak`, 속도는 `64.8 mm/s peak`다. isolator를 통한 계산 전달력은 `1.96 N peak`, force transmissibility는 약 `11.5%`다. mount당 등가 stiffness는 약 `947 N/m`, 정적 처짐은 `3.88 mm`다.

이 값은 rigid tray와 선형 isolator를 가정한다. 실제 고무의 비선형성, tray mode, eccentric harmonic, frame/camera mode와 fastener slip은 제외한다. 8 Hz 부근에서 dwell하지 않고 빠르게 통과하며, 회전수 ramp 중 변위와 frame acceleration을 감시한다.

## 이송속도와 체류량

입자 평균 이송속도는 정확한 해석값이 아니므로 tray peak velocity의 10–35%를 시험 전 범위로 둔다. 결과는 약 `6.5–22.7 mm/s`, 280 mm active deck 체류시간은 `12.4–43.2 s`다. 200 g/h에서 deck 위 평균 재료량은 약 `0.69–2.40 g`이므로 질량 처리능력보다 screen blinding과 긴 strip 자세가 지배할 가능성이 높다.

screen의 이상적 square-grid open area는 상단 약 `56.3%`, 하단 `36.0%`다. 실제 가장자리·지지대·wire 직조·부분 막힘으로 낮아진다. 6 mm flake/opening 비가 1.0으로 near-size blinding 위험이 크므로 6/8/10° slope와 25/30/35 Hz를 coupon에서 비교한다.

## 광학·프레임 gate

계산 전달력이 작아도 공용 frame resonance를 배제할 수 없다. sorter 동작 중 camera tunnel과 diameter gauge 위치의 3축 RMS가 `0.05 g` 미만임을 modal/운전 시험으로 확인하기 전에는 광학 측정과 sorter를 시간적으로 분리한다. 이 gate는 자동 batch scheduler와 Mega hard interlock 상태에 반영한다.

## 승인 전 시험

1. 5–40 Hz sweep으로 isolator resonance, tray/frame/camera 가속도와 bolt migration 측정
2. PLA/PET 3/6/12 mm와 긴 strip 혼합물로 세 배출구 질량수지·오분류·막힘 측정
3. 200/250/350 g/h에서 residence, carry-over, dust 누출과 screen 교체시간 기록
4. eccentric positive retention, guard, flexible chute boot, lid/service interlock 확인
5. isolator 파손 1개와 motor stall에서 tray가 frame/배선과 충돌하지 않는지 fault 시험
