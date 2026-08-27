# 문제 해결 — pre-release

| 증상 | 즉시 조치 | 가능한 원인 | 재가동 Gate |
|---|---|---|---|
| cutter 반복 jam | E-stop, lockout | 금지 이물, 두꺼운 solid PLA, dull cutter, feed 과다 | chamber 검사·원인 제거·guard 복구 |
| heater 상승률 비정상 | heater cutoff | sensor 이탈/open/short, MOSFET fault, insulation 문제 | 독립 sensor와 fuse 점검 |
| diameter 편차 | production pause | puller slip, melt flow, cooling, optical contamination | calibration과 transport-delay log 확인 |
| Pi 통신 단절 | Mega safe state 유지 | power/network/process crash | heartbeat와 self-test 통과 |
