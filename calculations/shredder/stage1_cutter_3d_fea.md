# Stage 1 커터 CAD 기반 3D 선형 정적 스크리닝

## 결론

실제 `exports/step/stage1_cutter_disc.step`를 Gmsh 4.15.2로 테트라 메시하고 CalculiX 2.23으로 푼 결과, 현재 커터 형상은 **정의된 60 N·m / 2치 분담 / 보어 고정 선형 모델**의 네 가지 스크리닝 기준을 통과했다. 이 결과는 가공 승인이나 물리 검증이 아니다.

| 항목 | 미세 메시 결과 | 기준 | 판정 |
|---|---:|---:|---|
| 최대 변위 | 0.01479 mm | ≤ 0.0667 mm | PASS |
| 최대 적분점 von Mises 응력 | 114.63 MPa | 참고값 | — |
| 임시 항복강도 650 MPa 기준 안전율 | 5.67 | ≥ 1.5 | PASS |
| 거친/미세 메시 최대변위 차이 | 4.77% | ≤ 5% | PASS |
| 미세 메시 반력 평형 오차 | 4.25×10⁻⁸ | ≤ 1% | PASS |

선형 탄성 비례로 현재 정의된 하중 경우도 함께 스크리닝했다.

| 하중 경우 | 시스템 토크 | 최대 변위 | 최대 von Mises | 임시 항복 안전율 |
|---|---:|---:|---:|---:|
| PET nominal tear | 6.3 N·m | 0.00155 mm | 12.04 MPa | 54.00 |
| PLA printed shell nominal | 27.0 N·m | 0.00665 mm | 51.58 MPa | 12.60 |
| PET folded/local double engagement | 36.8 N·m | 0.00907 mm | 70.30 MPa | 9.25 |
| PLA thick shell overload | 54.0 N·m | 0.01331 mm | 103.17 MPa | 6.30 |
| structural proof | 60.0 N·m | 0.01479 mm | 114.63 MPa | 5.67 |

이는 같은 경계·2치 분담·선형 재료 가정에서 60 N·m 결과를 비례 축소한 값이다. 재료 형상과 접촉 위치가 바뀌는 별도 비선형 최종 load case 해석은 아니다.

## 해석 계약

- 형상: 커터 OD 60 mm, root OD 38 mm, 두께 6 mm, 8치, 20 mm 키 보어가 들어 있는 실제 STEP.
- 요소: 4절점 선형 tetra(C3D4).
- 메시: 최대 요소 크기 2.0 mm(2,547 노드·8,940 요소)와 1.5 mm(4,647 노드·17,577 요소).
- 경계: tetra 외부 경계면을 추출하고, end face를 제외한 보어/키홈 원통면 노드의 병진 3자유도를 완전 고정한다.
- 하중: 전체 증명 토크 60 N·m에서 2치가 동시에 분담한다고 보고, +X 치형의 유한 tip patch에 절반 하중을 접선 방향으로 분포한다. 미세 메시의 평균 작용 반경은 29.21 mm, 적용 힘은 1,027.17 N이다.
- 재료: 탄성계수 210 GPa, 포아송비 0.30, 임시 항복강도 650 MPa인 열처리강 후보. 실제 강종·열처리·경도·성적서는 아직 TBD다.

JSON의 STEP SHA-256와 solver/version, 각 메시 node/element 수, 하중 선택, 반력 및 모든 판정값은 `simulation/structural/stage1_cutter_3d_fea.json`에 저장한다. `validation/test_stage1_cutter_3d_fea.py`는 두 메시를 실제로 다시 생성하고 두 솔버를 재실행한다.

## 해석 가능한 범위

이 모델은 기존 6×8 mm 이상화 tooth-ligament 손계산과 1D shaft beam 계산에서 빠져 있던 실제 CAD 치근·키홈 형상 효과를 3D 선형 탄성 수준에서 확인한다. 최대응력은 load patch 및 mesh에 민감할 수 있으므로 안전율은 설계 스크리닝 값일 뿐 허용응력 인증값이 아니다.

다음 항목은 **검증하지 않았다**.

- 커터와 PLA/PET 사이의 비선형 접촉, 마찰, 파쇄 진행
- 샤프트/키/보어의 접촉, 끼워맞춤, 미끄럼과 bearing compliance
- 충격, 소성, 균열, 피로, 마모, 잔류응력
- 재료 성적서, 열처리 품질과 실제 형상 공차
- cutter coupon torque test 및 완성 장치의 물리 시험

따라서 릴리스 체크리스트의 “detailed cutter/contact FEA와 모든 최종 load case” 및 물리 cutter coupon 항목은 계속 OPEN이다.

## 재현

```sh
nix develop --command python3 simulation/structural/stage1_cutter_3d_fea.py
python3 validation/test_stage1_cutter_3d_fea.py
```

두 번째 명령도 `gmsh`와 `ccx`가 PATH에 있는 `nix develop` 안에서 실행해야 한다. 스크립트는 임시 메시와 solver scratch만 `/tmp`에 만들고, 정규화된 JSON만 저장소에 남긴다.
