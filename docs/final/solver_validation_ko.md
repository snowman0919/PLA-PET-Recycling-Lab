# v0.8 solver 검증 보고

이 결과는 디지털 해석이며 실제 물리 시험·안전 인증이 아니다.

## 실행 환경

- FreeCAD 1.1.3: controlling solid 생성과 STEP 재수입
- Gmsh 4.15.2-git: 실제 CUT-03 STEP tetra mesh
- CalculiX 2.23: `OMP_NUM_THREADS=1` 구조/열팽창 해석
- OpenModelica 1.27.0 DASSL: mount travel와 LC09 scope 계약

## 판정

- LC04 actual FreeCAD plate: 0.001179 mm, medium→fine 2.544%, `DIFFERENT_METRIC_OR_MODEL`
- LC04 fine reaction force Y: 1736.533531 N / applied 1736.533695 N
- LC02 shaft: 0.082445 mm, 69.441 MPa, SF 2.556; force/moment residual 0.000005 N / 0.000018 N·m
- LC05 shaft: 0.088516 mm, 35.985 MPa, SF 4.933; force/moment residual 0.000026 N / 0.000003 N·m
- PET hot-zone free growth: 1.1661 mm, 1.3 mm travel margin 0.1339 mm
- selected radial/sliding mount regional SF: 2.090
- LC09 scope: spindle 143 mm, bearing spacing 88 mm, load at 40.5 mm, radial load 21.2390 N
- final STEP inventory: 76 files; solver-required 10 files are present and PASS

## 경계와 보류

- 축 moment residual은 출력된 절점 힘의 r×F만 포함한다. 회전 자유도 반력 couple은 추출하지 않았으므로 축방향 토크 평형의 독립 검증이 아니다.
- BC04 완전 고정은 채택하지 않으며 rear axial datum + front radial sliding guide가 release mount다.
- B31 mount 결과는 global axial restraint screen이다. 상세 sensor-bore/die-joint/thermal-fit closure는 별도 current digital qualification evidence를 따른다.
- `physical_validation_state: NOT_RUN`; 가열·가압·회전 시험은 수행하지 않았다.
