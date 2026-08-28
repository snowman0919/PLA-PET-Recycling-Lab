# Release slicer profile

- revision: `solid-manifold-openmodelica-v0.4`
- slicer: PrusaSlicer 2.9.6 (Nix-pinned)
- printer bed: 220 × 220 × 220 mm
- nozzle: 0.4 mm
- governing profile: `PPR_PrusaSlicer_2.9.6.ini`

ABS 부품도 geometry/plate 검증에는 같은 line-width profile을 사용한다. 실제 ABS 출력 시 수령한 filament의 권장 nozzle/bed/chamber 온도를 별도 material overlay로 적용해야 하며, 이 온도 변경은 형상·질량 gate를 우회하지 않는다.
