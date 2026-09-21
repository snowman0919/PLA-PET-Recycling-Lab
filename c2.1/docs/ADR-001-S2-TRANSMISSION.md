# ADR-001: C2.1 S2 단일 입력·역방향 출력 전동계

- 상태: **채택(디지털 운동학 반복만)**. 구매·가공·통전은 HOLD.
- 좌표계 `F0`: 고정 링 중심 `O`; `+Y`는 축/재료 폭 방향; `+X`는 고정 전단날 방향; `+Z`는 위. 수치 XZ 양의 각은 `+X→+Z`이며 물리적으로 `-Y`축 오른손 회전이다. 따라서 CadQuery `+Y` 회전에는 수치 각의 음수를 사용한다. `θ=π/2`에서 편심 중심은 `(X,Z)=(0,+e)`, 로터의 local `+X` 표식은 `φ=-π/(2q)` 때문에 `Z<0`로 이동한다.
- 증거: 아래 식·코드·CAD는 E2 결정론적 기하/운동학이다. 토크 용량, 수명, 분쇄 성능, 온도, 원가는 검증하지 않았다.

## 결정

고정 링 사이클로이드와 출력 핀/롤러를 사용한다. 공용 M1이 중심 입력축과 편심 저널을 `θ`로 구동한다. `q+1`개 고정 핀이 반력 부재이고, CAD에서는 사이클로이드 디스크·hook 로터·출력 창 web을 편심 중심 `E`의 단일 fused envelope로 표현한다. 실제 강체 체결은 별도 미결 인터페이스다. 출력 핀 캐리어와 출력축은 고정 중심 `O`에 놓인다. 독립 구동 자유도는 하나이며 별도 S2 모터는 없다.

`E_F0 = e[cosθ, sinθ]`, `φ_rotor = φ_output = -θ/q`, `ω_output = -ω_input/q`, `ω_ring=0`이다. 따라서 입력축과 출력축은 서로 반대 방향이다. 표시한 로터 재료점은 입력 `q`회전 뒤 반복한다. 한 번의 공전만으로 전체 표시점 주기를 주장하지 않는다.

출력 핀 중심은 `O` 기준 피치원 위에서 `φ`로 회전하고, 로터 출력 창도 같은 `φ`를 가지되 중심만 `E`만큼 이동한다. 핀-창 중심 편차는 항상 `e`, 필요한 diametral stroke는 `2e`다. 명목 e7, roller R5, 추가 방사 clearance0.20에서 창 반경은 `5+7+0.20=12.20mm`다. 로터/캐리어 공통 회전좌표에서 상대 벡터는 `R(θ/q)(-E)`이므로 속도는 `e|ω_input|(1+1/q)`다. q8,120rpm에서98.9602mm/s, 단일 무미끄럼 접촉을 가정한 롤러의 캐리어 상대 회전은 약-189rpm, 절대 회전은 carrier -15rpm을 더한 약-204rpm이다. 이는 정격이나 실측이 아니다. 0.20mm는 무간섭 명목 clearance라 정렬 위상에서 하중 접촉을 증명하지 않는다. backlash/phase take-up, 핀별 하중분담, 실제 잔류 미끄럼과 접촉압은 HOLD다.

축방향 구획은 `Y=-34..2mm` cycloid 반력, `4..44mm` 40mm 절삭/스크린/열 reference, `46..60mm` offset coupling, `64mm` 이후 output carrier/support로 나눴다. 구획 사이2mm nominal gap을 정적 all-pair BRep로 검사한다. 40mm 폭은 C2 reference 범위35~45mm 안이다. 다만 C2.1의 shear/screen/thermal CAD는 전동계 간섭을 보기 위한 solid envelope다. 실제 screen perforation/attachment, shear와 screen 센서 bore/mount, spreader interface/fins/분리 airflow는 통합하지 않았고 모두 HOLD다.

## 비교

|안|입력/출력 및 방향|편심 전달|판단|
|---|---|---|---|
|고정 링 사이클로이드(채택)|입력 `+ω`, 출력/로터 `-ω/q`; 1 DOF|출력 핀/롤러와 확대 창이 `e` 흡수|기존 C2 `-1/q` 운동을 직접 재사용하고 부품/축 수가 가장 적다. 로터가 기어 디스크 역할도 하므로 접촉·마모 검증 부담이 크다.|
|기계식 split dual-path|M1 뒤에서 공전 carrier와 자전 기어열을 분기; 비율/mesh parity로 방향 결정|정격 Oldham 또는 동등 offset coupling 필요|기어와 coupling을 독립 최적화할 수 있으나 축방향 길이, 지지, 마찰열, 비용과 미검증 인터페이스가 늘어난다. 큰 e/q 후보가 고정 링 공간을 초과할 때 재검토한다.|
|두 독립 동축 입력|두 속도를 독립 제어 가능|중공축/편심 중심 연결 필요|추가 구동 자유도와 별도 S2 구동을 만들므로 현재 사용자 제약에 맞지 않는다.|

외접 기어는 한 번 맞물리면 방향이 반전된다. idler 한 개를 넣으면 외접 맞물림 수가 1→2가 되어 최종 출력은 입력과 **같은 방향**이다. 따라서 “idler를 넣으면 항상 반대”라는 규칙은 사용하지 않는다. 회귀 검사는 `(-1)^외접맞물림수`를 고정한다.

## 토크·반력 경로

의도 경로는 M1 → 입력축/편심 저널 → 편심 베어링 → cycloid/hook 로터 → (a) 고정 링 핀/전후 금속 반력판과 (b) 확대 창/출력 롤러 → 출력 핀 캐리어 → 고정축 출력축/후방 베어링이다. 절삭 반력은 로터에서 고정 전단·챔버 지지로 닫혀야 한다. 출력축은 편심 로터 중심에 직접 닿지 않고 핀/창이 offset을 수용한다. 다만 CAD 로터는 한 개의 fused envelope이며 실제 볼트, 끼워맞춤, 축방향 retention을 모델링하지 않았다. 출력 캐리어는 별도 동력이 아닌 역회전 kinematic witness/load-extraction 후보이고, 명목 clearance 상태의 실제 하중 전달은 아직 증명되지 않았다.

이상 손실0 모델에서 출력에 작용하는 저항 토크 크기 `T_L`을 양으로 두면 `T_in=T_L/q`, `ω_out=-ω_in/q`이고 `P_in + P_load + P_fixed=0`이다. 고정 링 반력 토크는 `-(T_in+T_L)`이나 `ω_fixed=0`이므로 동력은0이다. 별도로 orbiting 로터 local 점 `p`의 속도 `v=d(E+R(φ)p)/dt`를 사용하여 절삭력 `F`와 외부 모멘트 `M`의 부하동력 `F·v+M·φdot`을 계산하고, 입력 일반화 토크 `Q=(F·v+M·φdot)/ω_input`과 독립 유한차분을 대조한다. 두 식 모두 이상 운동학 회계이며 효율·핀 분담·용량 산정은 아니다.

## 기각하지 않은 한계와 전환 조건

- 고정 핀 접촉응력, 로터/축 피로, 핀 분담, 백래시, 윤활, 열팽창, 베어링 L10, 롤러 속도/정격은 미검증이다.
- CAD의 bearing/roller는 치수 envelope일 뿐 MPN 또는 정격품이 아니다. 출력 창은 “rated Oldham”이라고 부르지 않는다. fused 로터 envelope의 실제 체결, bearing axial stop, circlip/shoulder, pin retention도 미모델/HOLD다.
- 가드 형상은 section envelope이고 완전 containment가 아니다. SVG는 생성 CAD section이 아니라 명시적 schematic이며, inspectable 형상은 full/exploded STEP다. E-stop, 인터록, 독립 과온 차단은 삭제하지 않는다.
- e/q 증가로 핀 링 공간·접촉 또는 열이 실패하거나 실험에서 편마모/감김이 확인되면 split dual-path와 정격 offset coupling으로 전환한다.
- PLA/PET/TPU 파괴, 처리량, 토크 이력, 입도, 체류, jam, 에너지는 보정 DEM/실험 데이터 전까지 `BLOCKED_PERFORMANCE_DATA`다.
