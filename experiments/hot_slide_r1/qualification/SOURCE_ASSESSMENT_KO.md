# HOLD 근거 조사 / 2026-09-09

현재 형상 HS-R1-S2와 본체의 재료·마찰·고온·추력 검토다. 공개 기술자료와 현재 부품의 성적서는 서로 다르다. `sources.json`은 실제 다운로드 성공/실패와 원문 해시를 기록한다. 원문은 source_cache/에만 두며 Git과 배포물에 넣지 않는다.

## 재료: 식별 가능한 근거와 적용 한계
ATI 17-7 Technical Data Sheet version1(2014), PDF p3 표는 상온 sheet/strip이다. RH950 전형 항복1380 MPa, TH1050 전형1205 MPa, CH900은 별도 냉간가공 후 시효 조건이다. 상온 수치를300°C 허용값으로 옮기지 않는다. p4는 A에서 RH/TH 처리 시 약0.004 in/in 치수 팽창을 기록한다. 이는 실제 가공품 측정값이 아니지만, 최종 열처리 후 R16.860±0.010을 검사해야 하는 이유다.

NACA TN4075(1957) TableIII, 인쇄 p7/PDF index7을 이미지로 확인해 `naca4075_selected.csv`에 전사했다. 재료는 Armco 0.05 inch(1.27 mm) TH1050, 압연방향, 온도30분 노출, strain rate0.002/min이다. 600°F(315.56°C)의0.2% 항복은148 및146 ksi이다. 현재3 mm CH900 후보의 보증값이 아니며, TH1050을 단순 대체해1100 MPa를 보증할 수 없다는 경고 근거다. 300°C에는 직접 측정점이 없다. 온도 보간은 추세 검토로만 표시한다.

HPM 공개 strip 공급 두께는0.0254–1.016 mm다. 이를3 mm 가공품 공급 증거로 사용하지 않는다. Elgiloy strip 문서는CH900의 전처리/시효·대표 인장강도를 제공하지만 현재 공급품의 고온 항복보증은 아니다.

원문:
- ATI: https://www.atimaterials.com/Products/Documents/datasheets/stainless-specialty-steel/precipitationhardening/ati_17-7_tds_en_v2.pdf
- NACA: https://digital.library.unt.edu/ark:/67531/metadc57021/m2/1/high_res_d/19930085071.pdf
- HPM: https://www.hpmetals.com/products/materials/stainless-steel-strip-foil/ss-17-7-ph
- Elgiloy: https://www.elgiloy.com/strip-17-7-ph-stainless-steel

## 시험 방법의 범위
ASTM E21-20 공개 개요는 고온 인장/항복 시험 대상이다. E328-26 공개 개요는 고정 변형에서의 하중 이완을 다룬다. G133-22는 ball-on-flat 왕복 마모 시험이며 극단 온도 범위는 제외한다. HS-R1 전체 접촉형상/300°C 시험을 G133 인증 시험이라고 부르지 않는다. 표준 전문을 구매·열람하지 않았으며, 내부 절차는 아래 원칙의 별도 공학 시험이다.

## 추력/체결
NSK51102 공식 자료: Ca10600 N, C0a16800 N, d15/D28/T9 mm. C/F는 동정격하중 비율이지 정적 안전율이 아니다. 카탈로그 형상/정격은 고온 윤활·경도·양방향 추력·전체 frame 적격성을 증명하지 않는다. NASA RP1228은 체결부 예압과 외력/열팽창의 설계 참고자료이며 현재 너트계수/고온 잔류 예압의 실측을 대체하지 않는다.
- NSK: https://www.nsk.com/engineering/products/bearings/ball-bearings/thrust-ball-bearings/single-direction-thrust-ball-bearings/51102-apn.html
- NASA: https://ntrs.nasa.gov/citations/19900009424

## 적용 방침
상온/타두께/타열처리/전형값/타접촉쌍을 현재 제작품의 보증값으로 승격하지 않는다. 근거가 확보된 사실과 미확정 가정을 입력 계약에서 분리한다. 공급자 문의안은 준비하되 발송·구매·통전을 하지 않는다.
