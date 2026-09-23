# C2.1 VP1 통합 제품 핸드오프

## 현재 결론

C2.1은 S1/S2 공용 M1의 1-DOF 전동계, S1→S2 능동 이송, 압출·냉각,
1.75 mm 풀러와 스풀 와인더, 가드·전장·제어를 하나의 VP1 조립으로
통합한다. 현재 기계 판독 결과는 `results/`, 전체 소재 경로 결과는
`../c2.2/results/full_machine/`, 최종 요약은 루트 `STATUS.md`가 기준이다.

디지털 조립·운동 결과는 소재 연속 이송 성공이나 물리 제작 승인이 아니다.
현재 STEP `b4acee8c…`/동일 해시 원본 USD `e484708c…`의 19,200-step,
8-cycle 연결 실행에서 S2 스크린 bounding-box 근접은 1/200이며
제품 소재 경로는 **HOLD**다. 이는 스크린 구멍 통과도 아니다.
구매·가공·통전, 물리 운전, main 병합은 명시적 승인 전 **HOLD**다.

## 구현된 제품 경로

- **전동계**: DRV-JACK은 절단 없는 단일 샤프트다. 체인 B는 잭샤프트에서
  S2로 이어지고, S1 헬리컬 기어 물림은 한 쌍만 유지한다.
- **S2**: q=8, e=7 mm. 참조 M1 58 rpm에서 단일 기어쌍 15/40과
  체인 B 24/12를 거친 편심축은 -43.5 rpm, 캐리어는 +5.4375 rpm이다.
  이는 미선정 모터의 참조 회전수에 따른 이상적 속도이며 실물 정격이
  아니다. 별도 S2 모터가 없고 독립 자유도는 하나다.
- **능동 슈트**: 과거 수동 계단, 패들/스크레이퍼와 얕은 오거는
  실패 이력이다. 현재 4회전 오거와 우선회 +Y 횡이송 스크루/쉘은
  BRep 비간섭이다. 별도 슈트 주입의 x335 통과는 22/22,
  캡 보어 y255 +Y 횡단은 18/22(횡단 후 유실 6/22)지만
  S1 픽업은 5/22다. 연결 시험의 스크린 근접은 1/200뿐이다.
  최종 판정은 `path_check.json`, `flow_localize/results.json`,
  연결 `run_vp1_final17/results.json`의 해시와 함께 읽는다.
- **풀러/와인더**: 1.75 mm 필라멘트용 스프링 니프, 양단 베어링,
  모터-드럼 토크 결합과 트래버스를 실제 조립 형상으로 포함한다.
- **전장**: PSU 24V 33A, 명판 800W. 500W는 소프트 운전 목표,
  792W는 전류 정격 강제 상한이다. 단계 제어 피크는 416W다.
- **펌웨어**: host self-test 19건을 통과한 전력 할당 로직은
  500W 초과를 경고하면서 792W까지 허용하고, 792W 초과 예약은 거부한다.
  target cross-compile, flash, 실제 통전은 실행하지 않았다.

## 설계 원본과 재생성

- `src/chute.py`, `src/drive_teeth.py`, `src/drive_kinematics.py`,
  `src/winder.py`, `src/electrical_bay.py`: 파라메트릭 원본.
- `src/build_machine_integration.py`: `cad/PPR_VP1.step` 생성과 BRep 검사.
- `src/build_machine_freecad.py`: 편집 가능한 FreeCAD 조립 생성.
- `src/build_system_bom.py`, `src/build_machine_wiring.py`,
  `src/build_firmware.py`: BOM, 배선, host 펌웨어 증거.
- `src/build_release_manifest.py`, `src/verify_artifacts.py`: 최종 해시 고정과
  패키지 검증. 결과 파일을 모두 만든 뒤 manifest를 마지막에 생성한다.

## 남은 HOLD

- M1/M2, 웜/휠, 축, 베어링, coupling의 토크·효율·피로·L10 정격.
- 실제 PLA/PET/TPU 처리량, 입도, jam, 파괴 에너지와 장시간 내구.
- 히터·모터·드라이버의 열평형, 케이블/fuse/contactor/terminal MPN 정격.
- 가드 판 두께, 체결, 파편 containment, interlock의 물리 검증.
- 제조 공차, 윤활, seal, axial retention, 유지보수 절차.
- 실물 E-stop, lid/service interlock, thermal fuse와 branch fuse 시험.

## 재현 순서

저장소 루트에서 관련 생성기를 실행한 뒤 테스트·검증을 수행하고,
`build_release_manifest.py`를 마지막에 실행한다. 구체적인 실행 환경,
통과 건수와 SHA-256은 `STATUS.md` 및 PR 실행 기록을 따른다.
