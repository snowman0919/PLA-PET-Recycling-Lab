# 좌표계 계약

FreeCAD/Fusion 공통 단위는 mm이다. 전체 조립 원점과 축은 FreeCAD 전역 좌표를 유지한다: +X는 장비 좌→우, +Y는 전면→후면, +Z는 테이블→상부다. 중력은 `(0, 0, -9.80665) m/s²`이다. 직접 부품 STEP은 해당 FreeCAD 함수의 local origin을 유지한다. 하중 방향은 각 LC JSON의 의미와 Fusion study 문서를 함께 적용하며, torque의 양의 방향은 오른손 법칙이다.
