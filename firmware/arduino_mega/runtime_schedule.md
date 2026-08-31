# Arduino Mega runtime schedule — v0.6.2

이 표는 실제 sketch의 cooperative scheduler와 ISR 경계를 기록한다. 물리 계측 전 worst-case execution time은 확인 대기이며, `PPR_DEBUG` build는 10 ms loop deadline overrun count와 최대 loop 시간을 1 s telemetry에 남긴다.

| 작업 | 목표 주기/한계 | 구현 | 실패 격리 |
|---|---:|---|---|
| hard safety input polling | ≤10 ms | 매 `loop()` 시작 시 `readInputs()` | 같은 supervisor cycle에 all-zero |
| puller/screw/spool tach snapshot | 20 ms | 외부/PCINT pulse를 atomic copy | 0.6–1.0 s timeout 후 fault |
| puller/spooler closed loop | 10–20 ms | 실제 elapsed time PI, supervisor loop | saturation/jam dwell 후 common rundown |
| fan 1/2 mux tach | 채널당 500 ms 관측 | A14 PCINT22, 250 ms마다 mux 전환 | 한 채널 손실도 cooling invalid |
| gauge/control | 50–100 ms 목표 | nonblocking ADC, requalification 판정은 200 ms cadence | invalid면 waste/rundown |
| MAX6675/heater input | 250 ms | 5채널 bit-bang, 채널당 16 bit | range/open fault, independent thermal chain 유지 |
| heater time proportion | 2 s window | applied-duty feedback + global allocator | phase cap, back-calculation anti-windup |
| traverse step | ≥2 ms step interval | spool turns×pitch target 추종 | limit/timeout hard fault |
| UI | 20–50 ms 목표 | edge polling, blocking wait 없음 | 명시 confirmation 없이는 restart 금지 |
| logging | ≥1 s | `availableForWrite()` guard | buffer 부족 시 log drop; safety loop 대기 금지 |

동적 할당은 사용하지 않는다. EEPROM은 boot read와 명시적 `CAL` 성공 시에만 write한다. `millis()` Timer0을 변경하지 않고, step pulse/MAX6675/serial 경로에 `delay()`는 없다. MAX6675의 1–2 µs bit timing만 `delayMicroseconds()`를 사용한다.

SRAM/flash evidence는 `validation/results/arduino_mega_compile.json`에 남긴다. 현재 compile은 flash 44,576 B/253,952 B, 전역 SRAM 2,089 B/8,192 B이며 stack/heap 여유는 6,103 B다. 이는 compile-time 수치이며 실제 worst-case stack 측정은 아니다.
