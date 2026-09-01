# Cooling airflow sensitivity — v0.6.2

- 방법: assumed fan curve와 quadratic duct pressure-drop network, seeded parameter sweep
- single-fan-loss median flow: 14.4 m³/h
- topology: fan electrical feedback(A4)는 전기적 부하만, mux된 fan tach는 회전만 증명한다.
- airflow inference: fan curve/duct model 출력이며 실제 airflow가 아니다.
- actual airflow: 미측정. duct blockage, filter fouling, leakage, strand 위치는 별도 sensitivity case다.
- 제어 연결: 상대 heat-transfer coefficient는 `(Q/35)^0.60`으로 기존 cooling time scale에만 연결한다. 단일 fan 손실은 실제 firmware에서 forming-chain fault다.
