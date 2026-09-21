# PPR - C2 진행 중

현재 개발 기준은 **C2.0**이다. 모터·최종 S2 형상·전체 원가·전체 제작도는 아직 미확정이다. **구매, 가공, 통전은 HOLD**다.

고정 제약: 보유24V800W PSU(240x120x65mm),500W 운전 cap, 공용 분쇄M1 한 개와 압출M2, PLA/PET/TPU, 전체 추가 구매/가공/배송/안전부품100,000원 soft limit, 본체700x420x520mm 상한.

## 현재 산출물

- `c2/docs/C2_ENGINEERING_NOTES.md`: 실제 변경, 가정, 결과, 미종결 항목.
- `c2/design/requirements.json`: 최신 요구조건 원본. 특정 모터를 고정하지 않는다.
- `c2/src/`: S2 매개변수 탐색, 결합 운동학, 핀 프로파일 검사, 열회로, 제어 참조, 비용 검토, 성능 학습 경로.
- `c2/results/`: 257개 형상 후보,108개 기본 열 민감도,5개 소형 핀 구속기구 프로파일 검사, 전력 배분1925건.
- `c2/cad/PPR_C2_S2_thermal_development.step`: 고정 전단날·센서 blind bore·금속 방열 새들/캡을 포함한 **S2 개발 모듈**. 전체 기계가 아니다.
- `c2/bom/`: 모터 후보 및136행 비용 검토 목록.125행 미견적이므로10만원 충족을 주장하지 않는다.
- `c2/experiments/`: 48개 형상 x3개 소재 =144개 미실행 성능 job manifest. 실제 DEM0건, 실물시험0건이다.

C2 성능 모델은 간극 수식의 학습으로 대체하지 않는다. GP/MLP 학습 경로는 실제 분쇄 응답과 보정/검증/원자료가 없는 현재 상태에서 **BLOCKED_PERFORMANCE_DATA**를 반환한다.

## 재현

```bash
python c2/src/run_study.py
python -m unittest discover -s c2/tests -v
python c2/src/build_cad.py
python c2/src/train_performance.py --backend gp
python c2/src/train_performance.py --backend mlp --out c2/results/mlp_run
python c2/src/verify_artifacts.py
```

수치 계산은numpy/scipy/shapely, CAD는CadQuery2.8.0이다. GP/MLP 선택 의존성은 `c2/requirements-research.txt`를 참고한다. 기본 데이터는 비어 있으므로 성능 모델 가중치는 생성하지 않는다.

## C1 보존

기존 루트의 `src/`, `design/assembly.json`, `design/parameters.json`, `cad/`, `bom/`, `results/`는 C1 기준SHA `0aa312c5be0ce566bc06f63fa4fdd5c9e7f3f47e`의 참고 설계다. 이 파일에 남아 있는 TT Motor 선정값/8:9 기구를 C2 확정값으로 읽지 않는다. C1 생성/검증 명령은 회귀검사용으로만 유지한다. 이전 pre-push 검사와 C1 CI는 제거하지 않았다.

자세한 보존 상태와 최종 커밋은 Git 기록이 기준이다. 원래 dirty worktree는 건드리지 않는다.
