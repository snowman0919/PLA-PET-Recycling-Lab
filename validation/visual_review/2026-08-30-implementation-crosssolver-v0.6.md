# v0.6 CAD 시각 검토 기록

- 날짜: 2026-08-30
- 검토자: parent Codex
- revision: `implementation-crosssolver-v0.6`
- 범위: 실제 생성 PNG의 pixel inspection; 물리 시험 아님
- 판정: `PASS_DIGITAL`

`compact_full_assembly_isometric.png`, `heater_and_hot_zone.png`, `forming_spool_motion.png`, `compact_section.png`을 직접 확인했다. Frame 내부의 공용 path와 metal load path가 유지되고, shield 제거 검사 뷰에서 3개 band heater, die cartridge, probe/lead, fuse와 고정 duct가 분리돼 있다. Section에서는 barrel–die–cooling/gauge/puller가 같은 중심선에 있고, forming/spool 뷰에서는 puller 뒤 solid guide, dancer, traverse와 full spool 경로에 불가능한 역굽힘이 없다.

blind5.5 bore의 0.5 mm 깊이 변경은 렌더 pixel에서 판별할 수 없으므로 FreeCAD B-Rep probe, RFQ dimension, STEP hash와 구조 계산으로 검증한다. 렌더는 donor cable bend, 실제 공차, bolt preload, 온도 변형이나 안전 기능을 입증하지 않는다.
