# 추가 부품 확인과 가격 근거

minimum_confirmation_bom.csv는 전체119행BOM이 아니라 설계 치수/전기interface에 직접 영향을 주는 잔여 확인13그룹이다. confirmed_available_quantity와 purchase_quantity를 비워 두었다. 미확인을0개보유 또는 전부구매로 바꾸지 않는다. PSU/프로파일/PLA/ABS/일반나사는 별도구매 목록에서 제외한다.

## 공개 가격의 의미
2026-09-09 공개 판매페이지/검색에 보이는 가격을 비교했다. 최저가라는 표현은 규격과 옵션을 확인한 검색범위의 표시가격에만 사용한다. 전세계 최저가나 한국 배송지의 최종 결제가격을 증명하지 않는다. 쿠폰/신규회원혜택은 사용하지 않았다. 배송비 빈칸은 무료가 아니다. 과거 배송예정일/캐시 재고는 현재 재고로 채택하지 않는다.
Mega완제품은 천일파츠13000원+3000원 표시, 비교 쿠팡15390원+3000원이다. BTS7960은 아이씨뱅큐5676원VAT포함이 현재 확인값이며 구문서4620원을 재사용하지 않는다. MAX6675 모듈은3800원+3000원 표시가 있지만 캐시가 오래되어 결제전 확인이 필요하다. 6905DD2020원과511024050원은 치수와 가격 후보이지 기존 SKF/NSK 정격이 입증된 대체품이 아니다.
모터와screw/barrel/cutter/히터의 실제 견적은 확보되지 않았다. 이 고비용 항목을0원이나 검색상 아무 소형모터 가격으로 채워 전체 견적을 만들지 않는다. 먼저 학교 재고를 확인하고 부족한 정확 규격만 발주한다.

## 접근 제한 대비
AliExpress의 GMP60 검색페이지 열기는 non-retryable access error로 실패했다. 원인이 봇차단이라고 단정하지 않는다. TDK 일부URL은429, heater1/DeviceMart 일부는timeout이었다. CAPTCHA 우회·계정로그인·프록시 회피를 시도하지 않았다. 동일 부품번호로 국내판매자 공개페이지와 제조사PDF로 전환했다. Ali 결제가격은 사용자가 앱에서 옵션/배송/수량이 보이는 화면으로 확인할 수 있으며 그 전에는 확정가격이 아니다.

## 정격 근거
TT Motor 제조사PDF의GMP60-60127 고속권선/47:1은24V 정격70rpm100kgf.cm(약9.80665Nm)이다. 이 값을 다른권선/다른감속비의 최저가격과 섞지 않는다. 현재 분쇄기 donor acceptance는 chain 전50~100rpm/연속6.59Nm 이상이다.
https://www.ttmotor.com/uploads/GMP60-609760127.pdf
MAX6675는Type-K 디지털 변환기다. Chiron thermistor를 해당 입력에 바로 연결하지 않는다. module과 올바른 비접지 probe는 별개다.
https://www.analog.com/en/products/max6675.html
PTC 일반원리는온도상승에 따라저항이증가하는자가조절이다. 제조사 일반문서는 사용자220V245C소자의출력/절연/부하온도를보증하지않는다.
https://www.tdk-electronics.tdk.com/en/373388/company/press-center/press-releases/press-releases/ceramic-components-ptc-heating-elements-for-electric-vehicles-/1196126

## 설계를 닫기 위한 한 번의 재고 회신
1. 분쇄/압출용24V 감속모터 보유 여부와라벨/축 치수.
2. Mega2560,분리형모터driver,전류센서,MAX6675/Type-K,heater스위칭모듈보유여부.
3. 배럴용24V히터 및Chiron cartridge의지름/길이/전압/W; PTC라벨도가능하면함께.
4. 6905/61905와51102,체인/스프로켓,안전차단부품,공구강/강봉/판재의보유여부.
5. 보유2020/2040길이별수량과PSU의DC OUTPUT라벨.
답변 전까지해당모터어댑터/히터bore/배선fuse를임의로확정하지않는다. 이미열간간섭이발견된후방collar는별도국부설계수정이필요하며특수spring후보의재료검증을재개하지않는다.
