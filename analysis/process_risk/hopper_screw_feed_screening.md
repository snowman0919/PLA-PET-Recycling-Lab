# Hopper/screw feed screening — v0.6.2

100 g/h는 nominal claim으로 유지하며 모델 결과로 상향하지 않는다.

- PLA: throughput P05/median/P95 = 43.8/89.2/170.8 g/h; starvation(<70 g/h) 29.7%; mean bridge probability 40.7%
- PET: throughput P05/median/P95 = 31.9/67.0/133.1 g/h; starvation(<70 g/h) 53.9%; mean bridge probability 54.2%

입력 범위는 bulk density, aspect ratio, wall friction, fill factor, pickup efficiency다. 실측 bulk density/flow coupon 전에는 `MODEL_INSUFFICIENT`이며 starvation 검출용 screw tach와 feeder interlock을 유지한다.
