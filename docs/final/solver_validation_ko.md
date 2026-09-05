# v0.8 solver 검증 보고

이 결과는 디지털 해석이며 실제 물리 시험·안전 인증이 아니다.

## 실행 환경

- FreeCAD 1.1.3: controlling solid 생성과 STEP 재수입
- Gmsh 4.15.2-git: 실제 CUT-03 STEP tetra mesh
- CalculiX 2.23: `OMP_NUM_THREADS=1` 구조/열팽창 해석
- OpenModelica 1.27.0 DASSL: mount travel와 LC09 scope 계약

## 판정

- LC04 actual FreeCAD plate: 0.001261 mm, medium→fine 2.543%, `DIFFERENT_METRIC_OR_MODEL`
- LC04 fine reaction force Y: 1856.543643 N / applied 1856.544176 N
- LC02 shaft: 0.084041 mm, 73.899 MPa, SF 2.402; force/moment residual 0.000376 N / 0.000021 N·m
- LC05 shaft: 0.039569 mm, 19.075 MPa, SF 9.305; force/moment residual 0.000026 N / 0.000001 N·m
- PET hot-zone free growth: 1.1661 mm, 1.3 mm travel margin 0.1339 mm
- selected radial/sliding mount regional SF: 2.156
- LC09 scope: spindle 143 mm, bearing spacing 88 mm, load at 40.5 mm, radial load 21.2390 N
- final STEP: 10 files, all clean-document reimport PASS (AP214 fallback)

## 경계와 보류

- BC04 완전 고정은 SF 0.206으로 실패하며 실제 mount로 채택하지 않는다.
- 선택 mount는 rear axial datum + front radial sliding guide이며 final assembly와 STEP/DXF/PDF에 반영됐다.
- B31 mount 결과는 global axial restraint 검증이다. sensor-bore 83.5 MPa는 폐형식 local screen이며 3D notch FEA가 아니다.
- `physical_validation_state: NOT_RUN`; 가열·가압·회전 시험은 수행하지 않았다.
