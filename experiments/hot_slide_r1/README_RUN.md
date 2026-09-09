# 재생성 및 검증

원격 mathcat에서 FreeCAD1.1.3, CalculiX2.23, Gmsh4.15.2 계열, Python/NumPy로 실행했다. exact version과 binary hash는 environment.json을 따른다. 라이브러리는 번들하지 않는다. 기존 도구 환경에서 새 사본으로 실행한다.

```sh
# 이 실험 폴더가 작업 디렉터리다. FreeCAD Python이 필요하다.
printf "import runpy; _=runpy.run_path('sliding_geometry_slotted.py',run_name='__main__')\n" | FreeCADCmd -c
OMP_NUM_THREADS=1 python3 solve_sliding_kinematic.py
OMP_NUM_THREADS=1 python3 solve_sliding_gradients.py
python3 evaluate_sliding_envelope.py
python3 test_protocol.py
python3 test_protocol_boundaries.py
printf "import runpy; _=runpy.run_path('test_fixture_geometry.py',run_name='__main__'); _=runpy.run_path('make_drawings.py',run_name='__main__')\n" | FreeCADCmd -c
typst compile handbook.typ HS-R1-S2_prototype_review_ko_v2.pdf
```

FreeCAD 콘솔의 exit code만으로 합격시키지 않는다. STEP 재수입 결과, 각 JSON/로그의 완료 marker와 actual file hash를 확인한다. 과거 result.json을 새 실행 결과처럼 사용하지 않는다.

`relief_candidate.py`는 해당 PPR 원본 geometry/parameter tree를 필요로 한다. 독립 압축 해제 폴더에서 임의 부모 디렉터리를 원본이라고 간주해 실행하지 않는다. manifest의 repository source hash가 맞는 PPR checkout의 experiments/hot_slide_r1에서만 재생성한다.

`raw_runs/`의 INP/FRD/DAT/log는 실제 머신에 남긴다. 배포 묶음에는 원시 파일 hash 목록을 포함한다. 전체 해석을 두 번 재실행했다는 주장은 하지 않는다. 같은 snapshot의 ZIP 반복 생성과 clean extraction만 별도 검사한다.

`validate_physical_test.py RECORD_JSON GEOMETRY_SHA256 REQUIRED_YIELD_MPA`는 측정 기록 검사만 한다. 실제 측정과 approval가 없는 template은 NOT_RUN이다. 코드가 기계의 제작/가열/운전을 승인하지 않는다.

실측 준비와 강화된 불확도·왕복·가열속도 검사는 COLD_TEST_READINESS_KO.md를 함께 읽는다. 두 시험 스크립트는 합성 시험 26개와 경계 회귀 시험 25개를 각각 실행한다.

검토용 r1 묶음 생성: `python3 package_review.py`. 두 합성 시험을 다시 실행하고 빈 실측 template을 확인한다. 기존 20260909.zip은 보존하며 20260909-r1.zip으로 생성한다. 이 명령은 실물 시험·구매·가열을 수행하지 않는다.
