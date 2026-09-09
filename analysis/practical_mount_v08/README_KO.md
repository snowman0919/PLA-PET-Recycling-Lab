# PPR 실용적 고온부 마감 검토

`DECISION_KO.md`는 사용자 결정에 따른 현재 작업 방향이다. 계산 근거는 `inspect_geometry.py`, `calculate.py`, `geometry.json`, `result.json`이다. 원본 기계 CAD를 새 설계로 교체하지 않고 읽기 전용으로 조사했다.

## 실제로 좁힌 문제
기존 열간 형상검사에서 전방 guide의 간극은 남았고, 겹침은 주로 후방 datum과 collar에서 발생했다. 자유 sliding을 논의하면서 모든 지지점에 배럴 앞끝의 팽창량을 적용하면 문제 위치와 필요한 이동량을 잘못 이해할 수 있다.

현재 BRep 기준 배럴 X95–375, rear shoulder 길이8 mm, guide X265–273이다. 기존 열모델의 shoulder 앞면 datum X367을 사용하면 guide까지 최대102 mm, 배럴 앞끝까지272 mm다. alpha=17e-6/K와 20→300°C의 동일 상한에서 guide 이동은0.48552 mm, 배럴 앞끝 이동은1.29472 mm다. 실제 접촉 datum이 반대 shoulder 면이면 별도 결과의 datum sensitivity를 따른다.

전방 bore34.6/배럴34.0의 명목 지름 간극은 같은 냉간 support 상한에서도0.43816 mm 남는다. 후방 bore34.1과 shoulder pocket44.1은 각각 지름 방향0.06184/0.10944 mm가 부족하다. 이는 단순 균일팽창/명목 치수 결과다. 공차, 중심 정렬, 실제 온도장과 마찰을 입증한 값은 아니다.

## 비용을 줄이는 선택
HS-R1-S2를 현재 기본 제작안에서 제외하고 그 12장 sheet, 고온1,222 MPa 재료 요구와 전용 인증 확장을 기본 일정에서 중단한다. 해당 요구는 폐기한 후보를 다시 선택할 때만 적용하며 기존 결과를 PASS로 바꾸지는 않는다.

새 부품을 만드는 대신 기존 후방 collar/retainer/지지부의 기능을 먼저 구분하고, 열간 여유와 중심 정렬을 함께 만족하는 최소 가공·shim·조립안을 선택한다. 단순히 구멍을 확대하면 정렬도 해결됐다고 하지 않는다. 전방 지지를 또 다른 정밀 spring 실험으로 바꾸는 것은 우선순위가 아니다.

## 중요한 정정
HS-R1-S2의 횡하중은 원래 carrier당25 N이었다. 1.24 kN을 그 spring에서 빼내면 요구 강도가 낮아진다는 앞선 설명은 정확하지 않았다. 현재 재계산은 잘못된 경로 설명을 바로잡고 실제 문제를 후방 접합부로 좁힌 것이다.

3/6 MPa는 저장소의 정상 모델/blocked-die 계산 사례이며 실측 압력이나 검증된 차단압력이 아니다. 16.22 mm bore 기준 축력은약620/1,240 N이다. 추력, 압력, 재료 항복강도를 같은 값처럼 쓰지 않는다.

## 재실행
FreeCAD Python에서 `inspect_geometry.py`를 실행한 뒤 일반 Python으로 `calculate.py`, `test_calculate.py`를 실행한다. 생성기 exit code뿐 아니라 JSON 상태와 원본 해시도 확인한다. 한정된 변경 그래프는 기존 graphify Python에서 `update_scoped_graph.py`로 갱신한다.

현재 본체 release=HOLD, 실물 시험=NOT_RUN이다. 이 변경은 합격기준 완화나 제작·통전 승인이 아니다. 추가 부품/서비스 구매는 없으며 기존 실험은 보존한다.
