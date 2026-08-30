# 운전 절차

Revision: `safety-orchestration-closure-v0.6.1`

1. Cold boot에서는 material이 `NONE`이다. 원료를 수동 확인하고 PET cap/neck ring/label/adhesive와 모든 금속을 제거한 뒤 PLA 또는 PET를 명시적으로 선택한다.
2. 한 batch의 material과 색을 정하고 외부 pre-dry를 수행한다. PLA 50 ±5 °C 4–6 h, PET 65 ±5 °C 6–8 h는 provisional 시작점이며 실제 moisture coupon을 우선한다.
3. 밀폐 용기로 옮겨 machine sealed hopper에 넣는다. Material 선택은 drive/current/gauge calibration을 대신하지 않으며 UI가 요구하는 교정 readiness를 별도로 확인한다.
4. Guard/interlock/thermal chain/E-stop, screen, flake bin, waste tray, cooling-current feedback, puller, spool과 dancer를 확인한다.
5. Shredder 시작은 verified drive/current calibration과 healthy driver/guard chain이 모두 필요하다. 시작 transaction이 거부되면 process는 `IDLE`, 모든 output은 0이다. 3회 bounded reverse 뒤에도 jam이면 latched fault다.
6. Extrusion 요청은 IDLE에서 fan-only startup probe를 먼저 시작한다. A4 feedback이 1.5 s 연속 healthy임을 입증하기 전에는 heater·screw·feeder·puller·spooler·traverse를 명령하지 않고, 3.0 s timeout은 FAULT/all-zero로 간다. 입증 후에만 `PREHEATING`을 commit하며, 온도와 gauge가 준비돼도 screw/feeder/puller는 자동 시작하지 않는다. Strand와 waste path를 준비한 작업자가 `READY_TO_EXTRUDE` 화면에서 명시적으로 arm/confirm해야 한다.
7. 정상 extrusion 중 spooler/traverse는 `spool_eligible=true`일 때만 허용되고 puller를 끌지 않으며 dancer만 추종한다.
8. 종료는 feed stop, bounded screw rundown, heater off, fan cooldown, disconnect와 0 V 확인 순서다. `COOLDOWN`은 T1–Tdie 네 채널이 모두 valid이고 60 °C 이하이며 cooling feedback이 정상일 때만 자동 `IDLE`로 돌아간다. 이 전이는 actuator 재시작이 아니며 다음 운전에는 새 명시 명령이 필요하다.

## PLA↔PET maintenance purge

Material 변경은 `IDLE`, feed=0, screw=0에서만 요청한다. 이후 process phase와 별도로 다음 material-session 순서를 지킨다.

```text
PURGE_PREHEAT_REQUIRED
→ PURGE_READY_CONFIRM_REQUIRED
→ PURGE_RUNNING
→ SCREEN_CLEAN_REQUIRED
→ HOPPER_CLEAN_REQUIRED
→ TEMPERATURE_TRANSITION_REQUIRED
→ FINAL_CONFIRM_REQUIRED
→ PLA_ACTIVE 또는 PET_ACTIVE
```

1. 기존 material을 active thermal profile로 유지하고 production spool을 제거하거나 분리한다.
2. `PURGE_READY_CONFIRM_REQUIRED`에서 물리 `START`로 purge feed 사용을 먼저 승인한 뒤, strand가 기존 waste tray/manual waste path로 향하는지 확인하고 별도 `CONFIRM`을 누른다. 두 명시 동작이 모두 없으면 purge screw/feed가 시작되지 않는다. 자동 diverter는 없다.
3. Purge preheat 요청도 fan-only startup proof를 통과한 후에만 heater를 허용한다. `PURGE_PREHEAT_REQUIRED`/`PURGE_READY_CONFIRM_REQUIRED`에서는 screw·feeder·puller와 전체 winding이 0이다. 독립된 feed 승인과 waste-path 확인이 모두 fresh safety preflight를 통과해 `PURGE_RUNNING`이 된 뒤에만 bounded low-RPM screw, 승인된 purge feed와 waste puller를 허용한다. Shredder/spooler/traverse는 전 구간에서 금지된다.
4. 완료는 최소 elapsed time, 최소 screw revolution evidence, stable temperature band, pressure/drive fault 없음, 작업자 시각 확인을 모두 요구한다. 현재 별도 screw tach가 없으므로 revolution evidence는 verified drive command/RPM에서 적분한 `COMMAND_DERIVED_ESTIMATE_NOT_MEASURED`이며 실제 회전수 계측으로 표시하지 않는다. Driver fault가 있으면 추정을 무효화하고 purge를 중단한다. 80 g/120 g 표기는 공학 추정치일 뿐 측정 purge mass가 아니다.
5. Screen과 hopper를 물리 lockout에서 차례로 청소하고 temperature transition 및 final confirmation을 수행한다. Pending material은 이 마지막 단계 전 active가 될 수 없다.
6. STOP/PAUSE로 고온 purge를 중단하면 session은 `PURGE_PREHEAT_REQUIRED`로 돌아가고, 정상 완료하면 `SCREEN_CLEAN_REQUIRED`로 간다. 두 경우 모두 motion/heater를 끄고 유효한 cooling feedback으로 T1–Tdie 모두 60 °C 이하가 될 때까지 `COOLDOWN`을 유지한다. E-stop은 즉시 all-zero이며, heater/screw/cooling fault로 중단되면 production eligibility는 false로 남고 원인 제거와 atomic clear 후 새 START와 startup probe가 필요하다.

## Forming-chain rundown과 재자격

Gauge invalid/uncertainty, cooling feedback, puller, spooler, dancer prelimit/hard limit 또는 winding safety에 영향을 주는 traverse fault가 발생하면 feeder·spooler·traverse를 즉시 끄고 production spool eligibility를 false로 만든다. Fault contract가 허용한 경우에만 screw와 puller가 bounded waste-discharge rundown을 수행하며 output은 waste tray로 보낸다. Heater는 bounded safe hold 뒤 cooldown한다. 일반 `FAULT`에서는 feedback이 유효한 cooling만 잔열 제거를 위해 유지할 수 있고, `COOLING_FAILURE` reason이나 E-stop에서는 cooling도 즉시 0이다.

재시작 전 gauge valid 20개 연속 sample, U95 ≤0.03 mm, `abs(d_mean-1.75) ≤0.05 mm`와 ovality ≤0.05 mm가 각각 10 s, puller 비포화, cooling feedback 정상, stable flow 뒤 die-to-gauge transport delay 경과를 모두 만족해야 한다. Delay는 248 mm와 nominal 약 100 g/h line speed에서 PLA 26.7 s/PET 28.6 s이며 200 g/h stretch 계산의 짧은 13.3/14.9 s를 qualification에 사용하지 않는다. 이때도 상태는 `READY_TO_RETHREAD`일 뿐이다. 작업자가 strand를 waste tray에서 production spool로 수동 rethread하고 명시적으로 확인하기 전 spooler와 traverse는 계속 금지된다.

Fault clear는 main disconnect/0 V/원인 제거 후 physical lockout key, E-stop reset, guard/thermal/driver feedback과 모든 subsystem clear preflight를 함께 요구한다. 하나라도 실패하면 어떤 latch도 부분 clear되지 않는다. 성공해도 actuator는 재시작되지 않으며 새 명시적 START/ARM 명령이 필요하다. Cutter/screw jam, screen 제거와 hot-zone service에는 E-stop만으로 부족하며 shaft mechanical block와 PPE가 필요하다.
