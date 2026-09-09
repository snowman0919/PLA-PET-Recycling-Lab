# 시험 목적과 판정 범위

## 수치 시험
기계 하중12회는 동일 STEP의 C3D10 선형 탄성, 힘·모멘트 평형, pad 변위와 mesh 수렴을 검사한다. 균일 팽창 사례는 외측 방사형 슬롯이 모델에서 불필요한 열구속을 만들지 않는지 확인한다. 구배6회는 prescribed temperature sensitivity이며 실제 heater/contact 열전달장을 구한 것이 아니다. 두께방향 단독 최대응력은 수렴 완료가 아니다.

6,144조합은 선정된 유한요소 compliance와 응력 선형 조합을 사용하는 대수 분석이다. 결과가 존재하는 모든 미시적 접촉·마찰·가공 공차를 해석한 것처럼 확장하지 않는다. 설치 예산0.04 mm는 실제 fixture에서 만족해야 하는 검사 요구다.

## 물리 기록 검사
`test_protocol.py`의26개 시험은 합성 fixture만 사용한다. 정상 형식 검사 외에 NOT_RUN, 잘못된 형상, 압력/회전, 승인/재료/계측 누락, 과하중, 위치/온도/시간/불확도 오류, stroke 부족, 보호장치 누락, 양면 온도차 초과를 거부하는지 확인한다. 합성 입력의 MEASURED 라벨은 parser test용이며 실제 측정을 했다는 증거가 아니다. 출력은 어떤 경우에도 machine_release=HOLD다.

## 형상
`verify_geometry_bridge.py`는 solver용 STEP과 제작검토 STEP의 symmetric difference와 체적을 직접 검사한다. 수치적으로 같은 BRep가 사용됐다는 사실만 검증한다. STEP 파일 해시가 다르더라도 그 이유를 exporter metadata와 geometry identity로 구분한다.

## 패키지
`package_review.py`는 실제 job 완료와 입력 해시, prototype source hash, STEP 대응, 파일목록과 clean extraction을 검사한다. 같은 snapshot에서 ZIP 두 번 조립한 결과만 비교하며 전체 solver/CAD pipeline 두 번 재생성이라고 주장하지 않는다. prototype이나 pressureless test 문서는 전체 PPR 제작 승인을 대체하지 않는다.

## 기록 경계 보강
`test_protocol_boundaries.py`의 25개 추가 합성 시험은 중복/음수 시각, 편도-only, 불확도 포함 이동폭·온도·near-envelope 하중, 잔류 변형, 허위 낮은 ramp 신고와 실제 표본 구배의 불일치, 비정상 입력 형식을 검사한다. 합성 51개 전체 통과는 물리 시험 수행을 의미하지 않는다.

## 패키지 r1
패키지 생성 때 두 시험을 실제 재실행한다. 실측한 것처럼 채운 template과 stale solver source는 격리된 사본의 부정 시험에서 거부되어야 한다. 최상위 payload는 명시적 목록으로 제한하여 임의 측정 JSON이 섞이지 않게 한다.

## r2 추가 시험
qualification/test_qualification.py의32개 및 test_strength_floor.py의8개는 합성 입력의 근거 적용범위/불확도/경계와 source 결박을 검사한다. 실제 material certificate 또는 마찰 측정을 수행하지 않는다. 추가 solver2회는 기존 선택 mesh의 axial traction 선형 응답이다. 하중분담/접촉 및 material3mm 고온 적격성은 여전히 HOLD다.
