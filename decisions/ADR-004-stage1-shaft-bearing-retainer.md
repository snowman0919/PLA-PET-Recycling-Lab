# ADR-004: Stage 1 20 mm shaft, 6004 bearing, combined retainer

- 상태: Accepted for proof baseline
- 날짜: 2026-08-28

## 맥락

17 mm shaft는 60 N·m proof load의 nominal SF가 약 2이지만 keyway sensitivity `Kt=1.6`을 적용하면 2 아래로 내려간다. 20 mm + 6204 bearing은 shaft에는 유리하지만 OD 47 mm counterbore 두 개를 중심거리 50 mm plate에 배치하면 중앙 web이 3 mm뿐이다. 개별 원형 bearing retainer도 서로 겹친다.

## 결정

- shaft: 20 mm keyed steel 후보
- key: 6×6 mm, 유효 길이 50 mm provisional
- bearing: 6004-2RS 후보, 20×42×12 mm
- plate: 42 mm counterbore, 36 mm through shoulder, counterbore 사이 web 8 mm
- retainer: bearing마다 원형 ring을 쓰지 않고 두 bearing을 함께 잡는 100×60×3 mm combined plate를 사용
- timing gear support: gear를 main plate와 세 번째 외부 plate의 6004 bearing 사이에 배치하여 cantilever bending을 제거

60 N·m, 유효반경 25 mm에서 단순 bearing 반력은 약 1.2 kN이다. SKF 자료의 6004 정격 `C=9.95 kN`, `C0=5.0 kN`과 비교하되 shock, contamination, misalignment, fit와 lubrication을 제외한 screening으로만 사용한다.

## 근거 자료

- [SKF bearings and mounted products catalog](https://www.skf.com/binaries/pub12/Images/0901d196807026e8-100-700_SKF_bearings_and_mounted_products_2018_tcm_12-314117.pdf): 6004 치수 `20×42×12 mm`, `C=9.95 kN`, `C0=5.0 kN`
- SKF bearing catalog: 정적 저속·shock load와 동적 load spectrum을 독립 검증해야 함
- 조회일: 2026-08-28

Target Budget 변형은 두 번째 support plate와 bearing 두 개를 생략할 수 있으나, gear overhang을 포함한 50 N·m trip 해석과 coupon torque가 통과할 때만 허용한다. Engineering Recommended baseline은 plate 3개, bearing 6개, combined retainer 3개다.

## 후속 Gate

- actual shaft material certificate와 key standard 확정
- counterbore fit coupon과 retainer preload drawing
- nominal 0.3/0.5 mm gear-side gap의 axial tolerance stack와 thermal growth 검증
- gear overhang 포함 shaft FEA
- cutter coupon torque spectrum과 bearing reaction 갱신
