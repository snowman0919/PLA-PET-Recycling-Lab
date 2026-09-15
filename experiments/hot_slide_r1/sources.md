# 재료 참고자료와 적용 한계

2026-09-09 확인. 아래 자료는 공급자 승인도면이나 가공품 성적서를 대체하지 않는다.

## Hamilton Precision Metals: SS 17-7 PH

https://www.hpmetals.com/products/materials/stainless-steel-strip-foil/ss-17-7-ph

제조사 자료의 온도 조건이 붙은 전형값과 공급/열처리 상태별 성질을 참고한다. 열처리/냉간가공 상태가 달라지면 강도가 크게 달라지므로 재질명만으로 spring 허용강도를 정하지 않는다. 이 페이지의 strip/foil 공급 두께 범위를 이번3 mm 가공품의 구매 가능성으로 확대하지 않는다. 고온1,100 MPa 보증 자료로 사용하지 않았다.

## ATI: ATI 17-7

https://www.atimaterials.com/Products/pages/ati-17-7.aspx

ATI의 제품/규격 확인용 원문이다. 실제 주문 가능한 형태, 최종 열처리 상태와 해당 사용 온도에서의 최소 항복강도는 공급자가 별도로 확인해야 한다. 인터넷의 다른 등급/전형값을 자동 대체하지 않는다.

## SKF: Axial load-carrying capacity

https://evolution.skf.com/axial-load-carrying-capacity/

위치결정과 열팽창 수용을 분리하고 접촉 마찰을 별도로 고려해야 한다는 기계 설계 배경 참고다. SKF bearing 정격이나 효율값을 이 spring prototype에 전용하지 않았다.

## 계산 입력

contract.json의 E=160–200 GPa, CTE 범위와 온도 조합은 감도 분석용 명시 가정이다. 실측/성적서로 바뀌면 같은 source chain에서 다시 계산한다. derived_requirements.json은 계산된 요구 강도이지 제공된 재료의 강도 인증이 아니다.
실험용 shoulder pin, carrier, base와 spring의 고온 성질도 자동으로 동일하게 취급하지 않는다. 현재 가열 적격성은 HOLD다.
