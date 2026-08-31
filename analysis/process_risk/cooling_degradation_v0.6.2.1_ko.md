# 냉각 열화 민감도 — v0.6.2.1

이 결과는 가정된 대류계수에 대한 해석 민감도이며 실제 airflow/온도 시험이 아니다.
fan tach는 회전만, 전류는 전기적 개연성만 증명한다.

- PLA 단일 fan: 100 g/h에서 75.5 °C, production controlled rundown 명령 0.0 g/h에서 25.0 °C (한계 48.0 °C).
- PET 단일 fan: 100 g/h에서 62.2 °C, production controlled rundown 명령 0.0 g/h에서 25.0 °C (한계 65.0 °C).

두 fan 모두 소실되면 feed/spool/traverse를 중지하고 forming chain을 controlled rundown으로 보낸다.
오염·누설·막힘·strand 편심의 수치는 commissioning 경계 설정용 해석 상한이다. 현재 firmware가 이 모델을 실시간 airflow 추정으로 사용하거나 자동 derate한다고 주장하지 않는다.
