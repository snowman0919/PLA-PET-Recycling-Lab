# P3 GGM 구동계 벤치 검증 절차

P3는 cutter, screw, heater를 장착하지 않은 상태에서 두 GGM 구동축의 **실제 속도·전류·토크 대응과 기계식 보호핀**을 교정하는 단계다. 실행에는 P0 PASS, P2의 적용 가능한 냉간 fixture/fit 검토, GGM 수령·mount compatibility PASS, 배선 점검, 독립 기준계측 준비와 별도 사용자 통전 승인이 필요하다.

## P3-0: 통전 전 preflight

모터 전원 연결을 검토하기 전에 `templates/p3_preflight.csv`의 21개 항목을 모두 실제 증거로 채운다. 각 행에는 작업자와 독립 검토자, timezone이 포함된 시각, 저장소 상대 evidence 경로와 SHA-256이 필요하다. `analyze_p3_preflight.py <p3_preflight.csv> --receipt-packet <P1 GGM receipt packet>`를 실행해 `PREPOWER_RECORD_CHECK_PASS`를 받아야 한다.

Preflight는 P2 냉간 fixture 검토, rigid metal load path, 12 mm/2x6201 test arbor, coupling/brake guard, cutter·screw 부재, heater branch 격리, 한 축씩만 통전하는 정책, BTS7960 두 채널, A0 shredder/A9 extruder motor-lead current wiring, F-SH 20 A/F-SCREW 10 A branch protection, de-energized hard-cut continuity, E-stop/positive-action interlock, 독립 current/RPM/torque 기준계측기와 P3 fixture 한정 승인 기록을 함께 확인한다. 수령 packet은 현 D02/D03와 `AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED`여야 한다.

`PREPOWER_RECORD_CHECK_PASS`는 **통전 허가가 아니다**. 분석기의 `motor_energization_authorized`와 `stage_p3_pass`는 의도적으로 항상 false다. 실제 P3 fixture 통전은 해당 evidence를 사람이 검토하고 그 실행에 대한 별도 승인을 내린 뒤에만 가능하다. Preflight가 실패하거나 evidence hash가 바뀌면 원인을 수정하고 다시 검사하며, bypass 값이나 임시 점퍼로 통과시키지 않는다.

## 치구

가능하면 프로젝트실의 traceable rotary torque transducer를 우선 사용한다. 없으면 `GGM_SH_Jackshaft`와 2×6201을 두 축에서 순차 재사용하고, 12 mm keyed test arbor에 Ø60×25 mm steel brake drum을 장착한 250.0±0.5 mm reaction-arm Prony brake를 쓴다. Brake reaction arm 끝의 0–200 N force gauge/load cell이 토크 기준이다. 8.0 N·m=32.0 N, 8.8–9.3 N·m=35.2–37.2 N이다. Drum/arm은 금속이며 출력물은 guard/센서 지지 외 구조 하중경로에 쓰지 않는다.

## P3-A: 전류센서 전기 교정

모터와 분리된 저전압 DC current loop에서 각 Hall sensor를 독립 DMM/shunt 기준과 비교한다. 최소 5개 점, 0 A 부근부터 4.6 A 이상까지 포함하고 useful range는 6 A를 넘기지 않는다. `reference_current_a`, ADC count, U95를 기록한다. 선형 fit 후 모든 점의 residual+U95가 0.10 A 이하여야 한다.

## P3-B: 무부하 축 확인

각 축을 별도로 guard 안에서 구동한다. SH는 K9G75C, EX는 K9G150C를 확인하고 3회 이상 no-load current와 output rpm을 기록한다. EX reverse command는 시험하지 않는다. 이상음·축 흔들림·coupling rub가 있으면 즉시 중단하고 P2/P3를 HOLD한다.

## P3-C: 동적 torque-current map

기계식 보호핀은 intact 상태로 두고 brake를 천천히 조여 실측 토크를 올린다. 권장 fit target은 1.5/3.0/4.5/6.0/7.8 N·m, independent holdout은 2.25/5.25/7.2 N·m이다. 실제 토크는 target이 아니라 force×실측 arm으로 계산한다. 각 loaded point는 안정값을 짧게 취득하고 brake/drum 온도 상승을 기록한다. SH holdout에는 F/R 둘 다 포함하고 EX는 F만 허용한다. holdout torque error bound는 0.40 N·m 이하다.

## P3-D: 보호핀 release coupon

이 시험은 **모터 OFF/lockout** 상태의 quasi-static 시험으로 한다. SH-F 3개, SH-R 3개, EX-F 3개를 서로 다른 coupon ID로 시험한다. 250 mm arm에서 release force U95까지 포함한 토크 구간이 8.8–9.3 N·m 안에 들어와야 한다. 파단 뒤 input/output pilot이 자유롭게 상대회전하고 hub/key에 영구손상이 없어야 한다. 목경 2.416–2.483 mm는 시작 가공 참고값일 뿐 합격값이 아니다.

## P3 판정

`analyze_p3_records.py`는 숫자 정합만 판정하며 하드웨어를 승인하거나 구동하지 않는다. 현장에서는 4개 P3 CSV와 preflight 결과를 같은 repository run directory 계열에서 유지한다. 먼저 `analyze_p3_preflight.py ... --output <p3_preflight_result.json>`으로 결과를 저장하고, 측정 후 `build_p3_inspection_packet.py --receipt-packet <P1 수령 packet> --preflight-result <p3_preflight_result.json> --records-dir <P3 기록 디렉터리> --output <packet.json>`로 authoritative inspection packet 구조를 만든다. Builder는 preflight 결과 파일 hash, exact receipt-packet hash, 당시 P0 HEAD/source bindings를 다시 검증한 뒤 각 P3 행의 evidence SHA-256, 작업자/시각, force/tach/current/arm 계측기 ID와 calibration ref를 확인하고 force×arm에서 torque/U95를 재계산한다. source packet의 physical authorization 값은 그대로 보존하며 새 승인을 만들어내지 않는다. 실제 P3 record acceptance는 `analysis/drive_acceptance_v08/manufacturing/inspection.py`가 동일 preflight chain과 별도 physical authorization을 모두 검증할 때만 가능하다. 보호핀은 8.8–9.3 N·m뿐 아니라 파단 뒤 자유회전과 hub/key 무손상도 authoritative 조건이다.

P3를 완료 상태로 넘길 때는 inspector가 생성한 exact packet/report를 보존하고 `templates/p3_stage_release.json`을 복사해 별도 run directory에서 작성한다. `approved_by`와 `independent_reviewer`는 서로 달라야 하며, `inspection_packet[_sha256]`와 `inspection_report[_sha256]`은 검토한 실제 파일을 가리켜야 한다. `validate_p3_stage_release.py <release.json>`는 report 내부의 canonical packet SHA-256, inspector source SHA-256, physical-action authorization 존재 여부를 다시 검사하고 현재 inspector로 packet을 재평가한다. 출력 `P3_STAGE_RELEASE_VALIDATED`는 P4 진입 선행조건만 충족하며 `p4_energization_authorized=false`, `machine_release=HOLD`를 유지한다.

## P3 보정값의 firmware handoff

`P3_STAGE_RELEASE_VALIDATED` 뒤에도 measured calibration을 곧바로 운전 펌웨어로 간주하지 않는다. `build_p3_firmware_profile.py --p3-release <release.json> --output-dir <empty-dir>`는 authoritative P3 packet에서 SH/EX current slope, zero ADC, no-load current와 gearbox torque gain을 다시 계산해 review-only `ggm_commissioning_generated.h`, shredder EEPROM `CAL CURRENT` 명령, provenance manifest를 만든다. 이 도구는 원본 firmware를 수정하지 않고 HEX build/flash 또는 EEPROM write를 수행하지 않으며, manifest의 `p8_entry_prerequisite`는 false다. 실제 P8 전에는 별도 application/build/readback 검증이 필요하다.
