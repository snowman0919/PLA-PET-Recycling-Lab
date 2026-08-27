# 정비 계획

모든 정비는 `docs/safety.md` lockout: E-stop→main disconnect/plug custody→0 V 확인→hot zone 안전온도 확인→shaft mechanical block→tool/fastener count→guard 복구 순서를 따른다.

| 주기/trigger | 검사·작업 | 불합격 조치 |
|---|---|---|
| 매 batch 전 | E-stop/lid/service/guard, purge catch, fines bin, cable·PE, optical window, spool retainer | 운전 금지·원인 교체 |
| 매 batch 후 | material holdup, screen, die face, roller debris, log/export, leak/odor | 오염 batch 격리·승인 세정 |
| 8 h | Cutter edge/chip, key/keyway witness, bearing play/temp, fastener paint mark, fan/filter | 분해검사·마모한계 갱신 |
| 40 h provisional | Gear/chain tension, shaft runout, screen fatigue, isolator crack, dancer/clutch calibration | 부품 교체 후 coupon 재시험 |
| 100 h provisional | Screw/barrel scoring·wear map, die/breaker, thrust bearing, heater clamp·wire insulation | 전문가 검사·치수 승인 전 금지 |
| 6개월 또는 변경 후 | E-stop single-fault, contactor mirror, interlock wire-open, sensor open/short, thermal trip/fuse, pressure trip | 전체 release fault matrix 재실행 |
| Camera/optic 이동 후 | 4-pin, field-position, distortion/homography, U95와 contamination | U95≤0.020 전 closed-loop 금지 |

주기는 실제 endurance·contamination data 전 provisional이다. 파손이 없다는 이유로 연장하지 않고, 3개 이상 batch의 상태추세를 검토해 변경한다.

## 세정·재질 전환

PLA/PET 전환은 같은 재질 색상전환과 다르다. Hopper, gate, auger, throat, screen pack, screw/barrel과 die의 holdup 경로를 분해/approved purge로 처리하고 이전 material mass balance가 끝나기 전 product batch로 전환하지 않는다. 밝은색→어두운색 순서를 우선하며 purge waste는 별도 표시·폐기한다.

Mirror/window는 scratch 없는 lint-free 도구와 승인 세정액만 사용한다. Cutter/screen에는 손을 넣지 않고 전용 brush와 retrieval tool을 쓴다. Heater/pressure seal에 용제나 grease를 임의 적용하지 않는다.

## 교체 후 재검증

Firmware/configuration, sensor, camera/optic, motor/driver, cutter/screen, screw/barrel/die, heater/insulation, safety relay/contactor, frame load path 중 하나가 바뀌면 관련 calibration과 coupon을 다시 수행하고 새 commit/batch revision을 기록한다. 동등품이라는 공급자 표현만으로 검증을 이월하지 않는다.
