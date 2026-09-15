# 전방 뚜껑 서비스 공간 재검토

기준 소스: f4aa7d720e70f865d8a1502c46272fa1732fcce2.
이 기록은 실제 FreeCAD 명목 형상의 비파괴 공간 검사다. 정식 CAD 승격, 가공 승인, 실물시험 완료가 아니다.

## 원래 목적과 크기

PLA/PET 단일 공용 경로와 같은 최종 실물을 유지한다. 200 g/h는 크기나 전원 증대를 정당화하는 강제 조건이 아니다. 별도 건조기, 두 번째 PSU, 추가 구동계를 도입하지 않는다. 기존 anti-reach chute, 호퍼 용량, 고온부 및 축간 구조는 변경하지 않았다.

기존 정식 배치의 작동 외형은 470 x729 x930 mm다. 현재 compact placement 검토안은 470 x700 x930 mm지만 왼쪽으로 뚜껑을 열면 X679 mm가 필요하다. 따라서 닫힌 외형뿐 아니라 뚜껑이 열린 때의 점유공간을 별도로 검사했다.

## 이번 FreeCAD 검사

기존 review.placement(base)의 266개 객체를 사용했다. 닫힌 뚜껑은 [5,322,900]..[209,526,908] mm다. 뚜껑만 Y 음의 방향으로 214 mm 평행 이동하면 열린 위치는 [5,108,900]..[209,312,908] mm다.

연속 이동의 보수적 전체 외곽은 [5,108,900]..[209,526,908] mm다. 기존 check_clear로 뚜껑 이외의 모든 원본 객체와 대조해 간섭이 없음을 확인했다. 닫힌 상태에서 반경98 mm 투입구의 미덮인 체적은0 mm3, 열린 상태의 투입구 점유 체적도0 mm3다.

가장 가까운 비호퍼 고정부는 FrameY910_0 및 GGM_FeederTopRail이며 명목 여유2.0 mm다. 이는 가공 오차, 휨 또는 손가락 공간의 검증값이 아니다. 레일과 체결부를 추가할 때 이 여유를 소비하면 다시 검사해야 한다.

이상적인 뚜껑 이동만 고려한 점유 외형은 470 x700 x930 mm로 프레임 안에 남는다. 기존 정식 모델의 왼쪽 개방 공간661 x729 mm 대비 평면 직사각형 면적은 약31.724% 작다. 작업자의 손, 공구, 배선, 레일/래치/인터록 외형은 포함하지 않았으므로 최종 설치공간의 감소율로 사용하지 않는다.

## 아직 남은 디지털 작업

전방으로 안내하는 레일의 단면/지지/체결, 뚜껑 이탈방지 stop, latch와 interlock 장착 상세를 설계해야 한다. 부품을 단순히 이동시키는 것만으로 이들을 구현했다고 표시하지 않는다. guard locking 필요 여부는 위험점 접근 시간과 실제 정지시간을 함께 검토해야 하며, 일반 interlock를 잠금장치로 표시하지 않는다.

이번 별도 service_envelope.py 작성 요청은 도구에서 차단되어 파일이 생성되지 않았다. 다른 경로로 해당 쓰기를 우회하지 않았다. 본 문서는 읽기·명목 공간 조사에서 확인한 사실만 보존한다.

PR 재발방지 hook은 유지했다. 현재 커밋의 실제 Git blob3228개를 분리한 CI-LIGHT72개 실행 항목이 PASS였다. 미커밋 파일을 검사에 섞지 않았고 알림 설정·메일·원격 필수 검사는 변경하지 않았다.

physical_validation_state=NOT_RUN; fabrication_authorized=false; energization_authorized=false; canonical_geometry_promoted=false.

## 구분에 사용한 제조사 자료

- IDEC의 guard interlocking 설명: https://www.idec.com/en-in/solutions/safety/law/iso-iec/iso14119 . 접근시간과 전체 정지시간의 관계로 guard locking 필요성을 구분한다. 이 자료는 PPR의 실제 정지시간을 증명하지 않는다.
- OMRON D4NS-1AF 사양: https://industrial.omron.eu/en/products/D4NS-1AF . key-operated interlock이지만 guard-lock 기능이 없는 예다. 본 검토에서 구매품으로 채택하거나 주문하지 않았다.
