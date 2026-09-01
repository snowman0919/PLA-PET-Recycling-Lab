# v0.6.2 완료 조건 감사

감사 대상은 `parallel-actuation-hardening-v0.6.2` 브랜치다. 이 문서의 PASS는 디지털 구현·가상 검증 범위만 뜻한다. 외부 Autodesk Fusion solve, 실물 가공·통전·유량·절단·필라멘트 품질 시험은 포함하지 않는다.

## 15개 완료 조건

|#|조건|판정|증거|
|---:|---|---|---|
|1|v0.6.1 Fusion baseline 불변|PASS|`run_binding.json` binding hash와 full-run frozen path hash guard|
|2|`FUSION_INPUT_DELTA=NONE` 또는 invalidating delta 격리|PASS|`validation/results/fusion_delta_classification.json`, `change_classification.csv`|
|3|실제 puller 신호 기반 saturation 연결|PASS|production `PullerSpeedController`, Arduino adapter의 `lastPullerSaturated()` feedback, supervisor rundown test|
|4|puller tach inner speed loop와 outer-loop 적분 gate|PASS|target/measured mm/s·RPM·error·PWM·tach·dwell, inner valid/non-saturated conditional integration test|
|5|실제 screw motion이 purge 완료를 gate|PASS|Hall tach abstraction, actual cumulative revolutions, insufficient/pass transaction tests|
|6|fan별 feedback과 단일/이중 손실 검출|PASS|A14 mux PCINT, `COOLING_FAN1_STOPPED`/`FAN2_STOPPED` host tests|
|7|heater applied-duty anti-windup|PASS|request→allocator→applied feedback, recovery 및 independent unexpected-rise test|
|8|dancer closed-loop spooler|PASS|radius sweep·disturbance recovery·tach jam tests|
|9|spool turn/pitch 기반 traverse|PASS|empty/half/full target, disabled transition, missed-limit latch tests|
|10|공통 forming rundown/requalification E2E|PASS|43 scenario/116 trace, gauge→waste→requal→manual rethread trace|
|11|Mega compile과 자원 여유|PASS|47,206 B flash(18%), 3,257 B global SRAM(39%), 4,935 B remaining|
|12|OpenModelica v0.6.2 shadow|PASS|24/24 DASSL scenario|
|13|shadow load를 Fusion 결과에 묵시 적용하지 않음|PASS|4개 LC-driving peak 모두 0% delta, rerun false, result scaling 없음|
|14|Fusion importer stale/mismatch 거부|PASS|7개 binding/rejection unit tests; 실제 결과는 pending|
|15|동일 HEAD CI-LIGHT/CI-FULL|PASS 요구|`validation/results/ci_light_v062.json`, `ci_full_v062.json`; 최종 commit 후 재실행|

## 실행 순서 26개 항목

|#|항목|상태|
|---:|---|---|
|1–5|fetch/state/binding 확인, v0.6.1 tag·archive, v0.6.2 branch, delta framework|DONE|
|6|timer/pin/resource audit|DONE|
|7–13|puller saturation/inner loop, screw tach, dual fan, heater anti-windup, spooler, traverse|DONE|
|14|forming fault/requalification 통합|DONE|
|15|production-class E2E host harness와 22개 high-signal evidence matrix|DONE|
|16|false-PASS mutation 7종|DONE|
|17–18|OpenModelica shadow 24개와 frozen envelope 비교|DONE|
|19|Fusion result importer/binding validator|DONE; external result pending|
|20|shredder/feed/airflow reduced-order risk screening|DONE|
|21|BOM·한국어 문서|DONE|
|22|CI-LIGHT|PASS|
|23|CI-FULL|PASS 요구; final HEAD 재실행|
|24|v0.6.2 branch push|최종 exact-head PASS 후 수행|
|25|Fusion import/correlation|`PENDING_EXTERNAL_EXECUTION`; actual bound result 0건|
|26|구매·발주·통전 금지|유지; 사용자 승인 필요|

## 해석 경계와 남은 외부 gate

- Process-risk 결과는 shredder `MITIGATION_REQUIRED`, feed `MODEL_INSUFFICIENT`, airflow `MITIGATION_REQUIRED`다. 실제 chip size·mass flow·airflow·생산 신뢰성 주장이 아니다.
- 실제 Fusion result가 없으므로 imported case는 0이고 correlation은 시작하지 않았다. `ACTUATION_HARDENING_COMPLETE`와 `FUSION_RESULT_INTEGRATION_PENDING`을 동시에 기록한다.
- `main` 승격은 Route A의 실제 Fusion correlation 완료 또는 사용자의 명시적 Route B Fusion-neutral merge 승인 전까지 금지한다.
- 조건부 예산은 178,729 KRW, reserve 포함 198,729 KRW이며 200,000 KRW cap 여유는 1,271 KRW다. Verified procurement budget은 `NOT_ESTABLISHED`다.
