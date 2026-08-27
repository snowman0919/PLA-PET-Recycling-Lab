# 안전 아키텍처와 현재 제한

이 문서는 설계 baseline이며 완성 장치의 인증서가 아니다. cutter, hot zone, 고전류 회로가 있는 실제 장치는 물리 검사와 fault injection을 통과하기 전 가동하면 안 된다.

## 위험 에너지와 차단

| Hazard | 예방 | 감지 | 독립 차단 | 복구 |
|---|---|---|---|---|
| cutter 접근 | 긴 굴곡/이중 gate, guard | lid/service switch | drive enable chain 개방 | lockout 후 수동 제거 |
| cutter jam/파편 | 금속 chamber, bounded feed | current/speed/vibration | stop → bounded reverse → latched fault | 전원 격리·보안경·도구 사용 |
| hot surface/melt | metal shield, insulation | zone sensor + guard sensor 후보 | thermal fuse + heater cutoff | 충분한 cooldown 확인 |
| thermal runaway | sensor 고정, derated heater | rate/plausibility/watchdog | thermal fuse와 E-stop cutoff | 원인 교체 전 reset 금지 |
| 과전류/단락 | wire gauge와 enclosure | branch current | branch/main fuse | fault 제거 후 fuse 교체 |
| Pi/Mega 통신 상실 | heartbeat | bounded timeout | Mega safe state | self-test 재실행 |
| spool/traverse 끼임 | low-force dancer, guard | current/limit switch | motor disable | 수동 해제 |
| 분진/증기 | 금지 재질, fines bin, 환기 | filter inspection | process pause | 청소·환기 |

## 안전 상태

`SAFE_OFF`에서 heater command는 0, cutter/extruder/puller/spooler enable은 해제되고 gate는 중력 또는 spring-safe 위치로 간다. fan은 전원이 안전한 경우 cooldown 목적의 제한 운전을 허용할 수 있으나 E-stop 회로의 실제 접점 구성 후 확정한다.

## startup self-test

1. E-stop reset 및 contactor feedback 일치
2. 모든 lid/service interlock 닫힘
3. 온도센서 open/short와 상식 범위 검사
4. motor current sensor zero 검사
5. encoder/limit stuck 검사
6. Pi heartbeat는 자동 모드에서만 필수
7. branch enable을 하나씩 짧게 검사하되 cutter는 재료 없이 guard가 닫힌 상태에서만 jog

## lockout

1. START/PAUSE가 아니라 물리 E-stop을 누른다.
2. PSU 입력을 차단하고 플러그 또는 disconnect를 작업자가 관리한다.
3. capacitor discharge와 0 V를 meter로 확인한다.
4. hot zone이 안전 온도 아래임을 별도 측정한다.
5. cutter는 shaft가 움직이지 않게 기계적으로 고정한다.
6. 정비 후 도구·shim·fastener count를 확인하고 guard를 복구한다.

## Release 전 필수 물리 시험

- E-stop single-fault test
- lid/service switch open 및 wire-open test
- 각 heater sensor open/short, stuck-on MOSFET 모사, thermal fuse 검증
- 각 branch short 대신 안전한 electronic load로 fuse/limit coordination 확인
- jam retry 횟수·시간·latched fault 확인
- Pi cable removal, serial corruption, watchdog reset 확인
- anti-reach probe와 파편 containment 검사
