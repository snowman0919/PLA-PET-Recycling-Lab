# Forming line visual/solid review — 2026-08-28

## 증거

- `forming_line_after_dual_view.png`
- `diameter_gauge_ray_proof.png`
- `renders/modules/forming_line_proof_{front,right,top,isometric}.png`
- `renders/modules/diameter_gauge_optical_proof_{front,right,top,isometric}.png`
- `simulation/forming/geometry_clearance.json`
- `validation/fabrication_review/forming_line_proof.json`

## 확인 결과

- 440 mm cooling tunnel은 146.667 mm 구간 3개와 80 mm fan envelope 3개로 분할되며 frame/fan과 의도하지 않은 solid intersection이 없다.
- Filament reference는 tunnel과 gauge shell을 접촉하지 않고 통과한다.
- Direct와 mirror-derived orthogonal reference ray가 각각 Ø1.75 mm filament reference를 가로지른다.
- Ø40×16 mm puller roller pair의 명목 nip gap은 1.50 mm이고 reference filament와 의도된 압착 overlap이 존재한다.
- Puller guard는 roller와 solid intersection이 없고 Ø30 mm odometer는 filament에 tangent contact한다.
- Full assembly keep-out은 760 mm forming line을 포함하도록 2,295×520×720 mm로 확장됐다.

## 시각 한계와 수정 이력

불투광 gauge enclosure가 내부 광학부를 가리므로 enclosure를 제거한 `diameter_gauge_optical_proof`를 별도 생성했다. Reference ray는 시선 교차만 증명하며 camera focus, mirror flatness, distortion, threshold와 U95는 교정 coupon 대상이다. 동일 색 STL render는 fan·duct·roller 경계를 제한적으로만 보여주므로 FCStd object와 geometry JSON을 함께 판독한다.

결론: rigid layout, airflow segment envelope, 두 광로 교차, nip/odometer 위치와 guard clearance는 proof 통과다. 실제 냉각 성능, 광학 불확도, tyre 압축·slip과 폐루프 직경 성능은 제작 및 coupon 시험 전 승인 상태가 아니다.
