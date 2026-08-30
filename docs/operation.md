# 운전 절차

1. 원료를 수동 확인하고 PET cap/neck ring/label/adhesive와 모든 금속을 제거한다. PLA는 50–100 mm로 사전 파단하고 PET 병은 납작하게 접을 수 있다.
2. 한 batch의 material과 색을 정하고 외부 pre-dry를 수행한다. PLA 50 ±5 °C 4–6 h, PET 65 ±5 °C 6–8 h는 provisional 시작점이며 실제 moisture coupon을 우선한다.
3. 밀폐 용기로 옮겨 machine sealed hopper에 넣고 UI에서 같은 material을 선택한다. 다른 material로 바꾸려면 IDLE, feed=0, screw=0에서만 wizard를 시작한다.
4. Guard/interlock/thermal chain/E-stop, screen, flake bin, spool과 dancer를 확인한다.
5. Shredder는 profile speed로 저 duty부터 시작한다. 3회 bounded reverse 뒤에도 jam이면 latched fault다.
6. Heater soak 후 low-feed purge, manual strand insertion, puller engagement 순서로 운전한다. Spooler는 puller를 끌지 않고 dancer만 추종한다.
7. 직경 U95가 미교정이거나 X/Y 차가 기준을 넘으면 feed를 즉시 정지하고 puller/spooler를 정지한다. Screw는 최대 10 s bounded rundown, heater는 최대 60 s reduced safe hold 뒤 cooldown으로 전환한다.
8. 종료는 feed stop, purge, screw stop, heater off, fan cooldown, 0 V 확인 순서다.

운전 중 material 변경은 금지한다. 전환 순서는 purge 확인 → screen clean → hopper clean → temperature transition → 명시적 final confirm이며 생략할 수 없다. Fault clear는 main disconnect/0 V/원인 제거 후 physical lockout key와 restart permission을 함께 요구한다. Cutter/screw jam, screen 제거와 hot-zone service에는 E-stop만으로 부족하며 shaft mechanical block와 PPE가 필요하다.
