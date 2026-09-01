# v0.6.2.1 OpenModelica shadow 결과

이 디렉터리는 `technical-blocker-closure-v0.6.2.1`의 축약 virtual shadow 결과다. 물리 시험이나 donor actuator의 실측 교정을 수행했다는 뜻이 아니다.

- P0-K에 이름이 열거된 시나리오: 21개
- P0-C dead-zone/saturation/tach-loss 추가 회귀: 3개
- 실제 실행: OpenModelica 1.27.0, DASSL
- 결과: 24/24 PASS

재현 순서:

```bash
python3 simulation/openmodelica/scripts/generate_v0621_shadow.py
omc simulation/openmodelica/scripts/run_v0621_shadow.mos
python3 simulation/openmodelica/postprocess/validate_v0621_shadow.py
```

`scenario_manifest.json`은 production 계약과 process surrogate 입력 해시를, `solver_execution.json`은 실행 결과 CSV 해시를, `scenario_trace.csv`는 각 시나리오의 대표 시점 trace를 기록한다. 전체 OMC raw CSV와 C build 산출물은 재생성 가능하므로 저장소 산출물에서 제외할 수 있다.
