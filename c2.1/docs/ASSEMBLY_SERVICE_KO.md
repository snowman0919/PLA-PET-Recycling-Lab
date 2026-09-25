# C2.1 전체 기계 조립·정비·시험 절차

## 적용 경계

이 문서는 C2.1 디지털 제작 검토 패키지용이다. `PPR_C2_1_machine_integration.FCStd`와 STEP은 C1 인터페이스 기준에서 기존 S2 44개 인스턴스를 제거하고 C2.1 S2 41개 객체를 넣은 결과다. 디지털 조립체는 196 solid 재수입, 변경 인터페이스의 양의 체적 관통 0건, 본체 630×408×508mm와 운전 envelope 839×408×508mm를 확인했다. 하중 변형·공차·열팽창·정비 동작 중 연속 충돌과 물리 조립은 확인하지 않았다.

C2.1 S2 로컬 좌표는 Z축 180도 회전 후 `(308.569464689, 299, 280)mm`로 이동한다. 이때 process 구간은 기계 Y=255..295mm이고 입력축은 X=308.569mm, Z=280mm에서 기존 ANSI35 12T 기준과 동축이다. 네 S2 금속 다리는 Y=170mm와 342mm의 지지판 접촉면으로 이동한다.

## 조립 순서

1. 전원과 모든 에너지원을 분리하고 개인 잠금표찰을 적용한다. 테이블·알루미늄 프로파일·금속 다리의 수평, 대각, 체결면 손상을 먼저 검사한다.
2. S1 cartridge와 보존된 drive 기준을 설치하되 축·sprocket을 최종 부품으로 간주하지 않는다. 입력축 동축도와 S1 여유를 실측하기 전 shim 또는 가공량을 확정하지 않는다.
3. 전후 C2.1 지지판과 고정 링, Ø8×140 명목 tie rod를 가조립한다. 베어링 MPN·fit·shoulder/circlip, 반력판 소재와 fastener grade/preload가 확정될 때까지 절삭·압입·최종 토크를 금지한다.
4. C2.1 rotor/process stack, 4mm perforated screen reference, split wear shell, thermal saddle/cap, output carrier를 조립성 확인용으로 배치한다. blade clearance는 출력 공차가 아니라 금속 shim으로 조절한다.
5. hopper/짧은 chute와 buffer를 연결하고 bridging 제거 접근로를 확인한다. 손이 절삭부에 닿는 개구는 anti-reach 검증 전 폐쇄한다.
6. 수평 extruder screw/barrel/die, thrust path, heater와 단열, cooling, diameter 측정 위치, puller와 spool을 순서대로 배치한다. 각 하중 경로는 금속 부품에서 bearing/plate, profile, table로 이어져야 한다.
7. 보호접지를 frame/guard/barrel/motor frame에 먼저 연결한다. 그 뒤 branch fuse, 안전 contactor, dual-channel E-stop/lid/service interlock, 독립 manual-reset overtemperature, one-shot thermal fuse, driver와 sensor harness를 배선한다. MCU는 안전 차단의 유일 수단이 아니다.
8. guard·배선·호스의 정비 sweep를 확인하고 마지막에 동력부 cover를 설치한다. 현재 CAD의 guard는 containment 인증 형상이 아니므로 제작 승인 대상이 아니다.

## 정비와 잠금

정지 명령만으로 접근하지 않는다. 주 전원 분리, 잔류 전압 확인, 회전체 정지, heater 냉각, 압출 잔압 제거, 개인 잠금표찰의 순서를 지킨다. screen 청소, jam 제거, blade/shim 조정, sensor 교체에는 shaft의 물리적 회전 방지와 heater 회로 격리가 모두 필요하다. 잠금 해제 전 공구·shim·시편 수량, guard, PE, interlock actuator와 독립 과온 복귀 상태를 2인 확인한다. 자동 재시작과 역회전 경로는 허용하지 않는다.

## 단계별 실제 시험

모든 시험은 현재 `DID_NOT_RUN`이다. 정확한 부품과 한계값이 정해진 뒤 위험성 평가와 사용자 승인을 받아 순서대로 수행한다.

1. 무통전 치수검사: 부품 라벨, 재질 증명, 축경, bore, bearing fit, runout/TIR, blade shim gap, fastener engagement, 접지 연속성의 원자료를 기록한다. 불일치는 가공으로 숨기지 않는다.
2. 안전회로 단독 저에너지 시험: 각 E-stop/lid/service 채널의 단선·교차단락, EDM, manual reset, 독립 과온, one-shot fuse 회로를 시험한다. 어떤 단일 fault에서도 contactor가 재투입되거나 자동 시작하면 FAIL이다.
3. actuator 분리 상태 I/O 시험: sensor open/short/stale, fan tach loss, current/rpm mismatch, buffer high를 주입한다. 출력은 fail-closed여야 하며 reset만으로 구동이 시작되면 FAIL이다.
4. 수동 회전 시험: lockout 상태에서 전 주기 간섭, screen/rotor, output pin/window, seal과 shaft retention을 확인한다. binding, 금속 접촉, axial migration은 FAIL이다.
5. 제한 전원 무부하 시험: 정격이 확정된 fuse/current limit 아래에서 짧은 단계로 수행하고 전류·rpm·진동·온도 원자료를 저장한다. guard와 원격 차단 없이 실행하지 않는다.
6. 열 시험: PLA, PET, TPU를 혼합하지 않고 건조 조건·질량·주변온도를 기록한다. 여섯 온도 채널, motor/gearbox, fan curve, 외벽·방열판 온도와 sensor delay를 보정한다. 독립 과온 차단을 실제 확인한다.
7. 재료 시험: 교체식 coupon부터 시작해 투입/회수 질량, 2.5~5mm 질량수율, oversize/fines/sliver, throughput, torque/current/rpm, jam, 체류시간, J/g를 원자료로 남긴다. 100g/h와 목표 입도는 실측 전 보장값이 아니다.

각 단계의 합격값은 선정 부품 datasheet와 위험성 평가가 정한 뒤 `OPEN_ACTIONS_KO.md`를 갱신한다. 앞 단계 실패 시 다음 단계로 진행하지 않는다.

## 현재 금지 사항

구매·외주 발주·가공·통전·구동·target firmware flash·main 병합은 승인되지 않았다. RFQ 도면의 치수는 명목값이며 datum, fit, GD&T, 공차, 소재 grade, 열처리, 표면처리는 HOLD다. KiCad 자료는 기능 net 일관성 자료이고 MPN/제조사 terminal 번호/정격이 없어 제작 회로 검증이 아니다.
