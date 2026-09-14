# 고온부 입력 결박 보완

이 변경은 Z1 분포 열모델의 완성이 아니다. 기존 팽창/구속 screening의 실제 입력 불일치를 먼저 수정한다. 배포 rc1과 새 작업트리의 도면을 혼용하지 않는다.

## 기존 문제와 수정

Modelica의 1.3 mm 상수를 제거하고 final_v08.json의 cold_axial_travel_mm를 CADParameters 생성기를 거쳐 읽는다. 컴파일 init.xml의 값뿐 아니라 원시 CSV의 팽창량+잔여 이동량도 동일한 현재 CAD 값인지 검사한다. 구형 컴파일 값, runtime override, 빈 기록, NaN/무한대는 거부한다.

CalculiX hot_mount_deck는 geometry_manifest의 GGM 통합 native 좌표를 읽는다. 배럴 뒤끝을 로컬0으로 두며 rear datum/front guide에 실제 절점을 삽입한다. 압력 thrust는 가이드가 아니라 die 쪽 TIP에 적용한다. CAD와 final_v08.json의 두 지지점이 다르거나 좌표가 유한하지 않으면 거부한다. 16항목을 초과하는 NSET은 기존 nset helper로 분할한다.

## 해석의 한계

- Modelica는 여전히 시정수60초의 균일 온도 팽창 모델이며 inherited83.5 MPa 응력을 사용한다. Z1 폭, 접촉 전도, PID 또는 실제 열보호 성능을 검증하지 않는다.
- CalculiX는 기존 등가 직사각형 B31 단면과 rear rotational clamp를 유지한 prescribed-temperature 비교다. 실제 중공 단면의 국부 응력, 레일 접촉/미끄럼, 고온 물성 또는 전체 기계 하중을 승인하지 않는다.
- 열접촉 계수, 외피 온도, support sink 및 소재 인증은 임의 확정하지 않는다.
- 45->40 mm, 동일100 W의 명목 접촉면적 기준 발열밀도 비율은1.125다. 온도 상승 비율이1.125라는 뜻은 아니다.

## 검증

validation/test_hot_mount_geometry_binding.py와 test_hot_travel_binding.py가 정상 결박과 부정 입력을 검증한다. 실제 solver 재실행 결과는 별도 보고서의 정확한 로그/입력 해시를 따른다. 테스트 통과와 해석 qualification 통과는 별개다.

physical_validation_state=NOT_RUN, fabrication_authorized=false, energization_authorized=false, global_release=HOLD를 유지한다.

## 참조

- OpenModelica 공식 simulate/compiled-parameter 인터페이스: https://git.openmodelica.org/Documentation/OpenModelica.Scripting.simulate.html
- Ovako42CrMo4 물성은 전형값이며 SCM440 납품재 인증이 아니다: https://steelnavigator.ovako.com/steel-grades/42crmo4/
- 밴드히터의 설치·클램핑·접촉은 발열밀도 외의 설계 입력이다: https://www.tempco.com/Duraband-Heaters.htm
