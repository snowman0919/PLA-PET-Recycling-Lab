# 문제 해결

| 증상/fault | 즉시 안전상태 | 확인 순서 | 재가동 gate |
|---|---|---|---|
| `FAULT_ESTOP` | High-current bus 차단 | E-stop 두 channel·reset·aux wire | monitored reset+SELF_TEST |
| `FAULT_CONTACTOR` | Main disconnect/lockout | mirror contact·coil·welded pole·D23 polarity | 자격 continuity/contact test |
| Lid/service/guard fault | 모든 위험 motor off | cover 정렬→positive-opening switch→wire open | hardware chain+Mega aux 모두 healthy |
| Thermal/sensor fault | 모든 heater off; 안전하면 cooldown | sensor 고정/open/short→driver welded-on→trip/fuse | dry-block+fault injection 재교정 |
| Pressure warning/trip | Feed/heater/motor off; relief catch 접근 금지 | screen/die clog→transducer→mechanical relief | pressure 0+원인 교체+qualified leak/proof |
| Airflow fault | Extrusion pause | fan power→filter/duct→occupied-path velocity→D28 | 2.5/4.0 m/s map 통과 |
| Cutter 반복 jam | E-stop·lockout·shaft block | 금지 이물→실질두께→edge→clearance/shim→feed | chamber/guard 검사+저에너지 coupon |
| Extruder current/torque 상승 | Feed 감소 후 latched stop | dry quality→bridge→barrel temp→screen pressure→bearing | dyno/pressure trace 정상 |
| 직경이 굵음/가늘음 | Product PAUSE | gauge contamination/calibration→puller slip→flow/feed→cooling→delay | U95/encoder/step response 통과 |
| Ovality 증가 | Product PAUSE | dual-view sync→냉각 비대칭→nip force/tyre→spool tension | ovality ≤0.05 mm 30 min |
| Pi 통신 단절 | Mega 760 ms 이내 safe output | Pi undervoltage→USB→process log→CRC | stable HB+local reset+self-test |
| Camera dropout/오염 | 3 s 후 PAUSE | exposure/focus→backlight→window/mirror→frame rate | 10 Hz+4-pin/contamination test |
| Dancer end/traverse spill | Spooler off; puller/feed pause | thread path→spring/sensor→clutch→home/end | 0.5±0.1 N+70 mm travel+1 kg coupon |
| 비정상 냄새/연기/불꽃 | 즉시 E-stop+main disconnect+대피/환기 | 임의 재통전 금지; 자격 전기/화재 조사 | 원인 부품 교체+전체 fault test |

Fault bit와 state/phase는 `electronics/protocol/frp1.md`, timing은 `simulation/control/safety_timing.json`을 참고한다. 로그를 지우거나 fault를 software에서 우회하지 않는다.
