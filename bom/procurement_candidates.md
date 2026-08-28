# 구매처·가격 후보

조회일: 2026-08-28. 상태: **비교 후보 / 주문 미승인**.

85행 시스템 BOM 중 BUY 32행을 모두 `procurement_routes.csv`에 연결했고, 그중 17개 Part ID에 실제 공개 페이지 또는 Playwright 검색 증거를 기록했다. `PRIMARY_CANDIDATE`와 qualification/sizing 후보는 가격·배치 계산용 기준일 뿐 구매·안전 적합성 승인이 아니다.

| Part ID | 공급처 | 후보/MPN | 관측가 | 재고 | 선택 상태 | 링크 |
|---|---|---|---:|---:|---|---|
| GAU-CAM-001 | Raspberry Pi official | Raspberry Pi Camera Module 3 standard / `Camera Module 3 Standard` | 25.00 USD | UNKNOWN | PRIMARY_CANDIDATE | [제품/검색 결과](https://www.raspberrypi.com/products/camera-module-3/) |
| SAF-REL-001 | AutomationDirect | Dual-channel safety relay / `LG5925-48-61-24` | 143.00 USD | UNKNOWN | PRIMARY_CANDIDATE | [제품/검색 결과](https://www.automationdirect.com/adc/shopping/catalog/safety/safety_relay_modules/2-channel_e-stop_-z-_safety_gate_relays/lg5925-48-61-24) |
| GRN-BRG-001 | DigiKey | 6203 contact-sealed bearing 17x40x12 / `6203-2RS-GLD` | 2660 KRW | 4267 | PRIMARY_CANDIDATE | [제품/검색 결과](https://www.digikey.kr/en/products/detail/mechatronics-bearing-group/6203-2RS-GLD/9608381) |
| ELE-BUCK-001 | DigiKey | 30 W DIN rail isolated 24 V to 5 V converter / `DDR-30G-5` | 42644 KRW | 248 | PRIMARY_CANDIDATE | [제품/검색 결과](https://www.digikey.kr/en/products/detail/mean-well-usa-inc/DDR-30G-5/8681204) |
| SAF-EST-001 | DigiKey | Dual-channel twist-reset E-stop / `A22E-M-02` | 143001 KRW | 830 | PRIMARY_CANDIDATE | [제품/검색 결과](https://www.digikey.kr/en/products/detail/omron-automation-and-safety/A22E-M-02/549568) |
| SAF-REL-001 | DigiKey | 2 safety outputs plus auxiliary safety relay / `G9SE-201` | 425730 KRW | 216 | ALTERNATE | [제품/검색 결과](https://www.digikey.kr/en/products/detail/omron-automation-and-safety/G9SE-201/7495167) |
| SAF-INT-001 | DigiKey | Positive-opening guard switch body / `D4NS-2AF` | 126007 KRW | 6 | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.digikey.kr/en/products/filter/interlock-switches/1060) |
| SAF-THM-001 | DigiKey | 72 C one-shot thermal cutoff / `SDF DF072S` | 1384 KRW | 8027 | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.digikey.kr/en/products/detail/cantherm/SDF-DF072S/1014753) |
| SAF-THM-001 | DigiKey | 184 C one-shot thermal cutoff / `SDF DF184S` | 1384 KRW | 20027 | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.digikey.kr/en/products/detail/cantherm/SDF-DF184S/1014767) |
| COOL-AIR-001 | DigiKey | 80x25 mm 24 V ball-bearing fan / `F8025E24B-FSR` | 19192 KRW | 1240 | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.digikey.kr/ko/products/detail/mechatronics-fan-group/F8025E24B-FSR/5209762) |
| COOL-AIR-001 | DeviceMart | 80x25 mm 24 V ball-bearing fan / `MC001586` | 39765 KRW | 0 | ALTERNATE | [제품/검색 결과](https://www.devicemart.co.kr/goods/view?no=12068635) |
| DRY-SEN-001 | DeviceMart | Three-wire stainless PT100 probe / `3290` | 24420 KRW | UNKNOWN | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.devicemart.co.kr/goods/view?no=14601237) |
| EXT-SEN-001 | DeviceMart | 350 C PT100 probe / `R15-4A-M12-3-150` | 73997 KRW | 0 | PARTIAL_ASSEMBLY | [제품/검색 결과](https://www.devicemart.co.kr/goods/view?no=13286077) |
| ELE-HTR-DRV | DeviceMart | 20 A AC-output solid-state relay / `CKRD2420` | 145024 KRW | 22 | REJECTED | [제품/검색 결과](https://www.devicemart.co.kr/goods/view?no=8837009) |
| SHR-BRG-001 | AliExpress | Two-piece 6004-2RS bearing search result / `6004-2RS` | 9530 KRW | UNKNOWN | SAMPLE_ONLY | [제품/검색 결과](https://ko.aliexpress.com/item/1005009127758758.html) |
| SHR2-BRG-001 | AliExpress | Two-piece 6004-2RS bearing search result / `6004-2RS` | 9530 KRW | UNKNOWN | SAMPLE_ONLY | [제품/검색 결과](https://ko.aliexpress.com/item/1005009127758758.html) |
| GRN-BRG-001 | AliExpress | Two-piece 6203-2RS bearing search result / `6203-2RS` | 6720 KRW | UNKNOWN | SAMPLE_ONLY | [제품/검색 결과](https://ko.aliexpress.com/item/1005006330857857.html) |
| SRT-ISO-001 | AliExpress | M5 rubber bobbin isolator search result / `M5 rubber mount` | 1405 KRW | UNKNOWN | SAMPLE_ONLY | [제품/검색 결과](https://ko.aliexpress.com/item/1005002994598621.html) |
| COOL-AIR-001 | AliExpress | Delta PFB0824EHE claimed original fan search result / `PFB0824EHE` | 25600 KRW | UNKNOWN | SAMPLE_ONLY | [제품/검색 결과](https://ko.aliexpress.com/item/1005012625321003.html) |
| SAF-CON-001 | Mouser | AFS safety contactor with fixed mirror auxiliaries / `AFS30-30-22-11` | 316.39 USD | 1 | QUALIFICATION_CANDIDATE | [제품/검색 결과](https://www.mouser.com/en/ProductDetail/ABB/AFS30-30-22-11?qs=iLKYxzqNS76HP0X0B0esXA%3D%3D) |
| SAF-FUS-HLD | DigiKey | Class CC finger-safe one-pole DIN fuse holder / `CHCC1DU` | 95.10 USD | 0 | SIZING_CANDIDATE | [제품/검색 결과](https://www.digikey.com/en/products/detail/eaton-bussmann-electrical-division/CHCC1DU/2767773) |
| ELE-HTR-DRV | DigiKey | IP20 isolated GN-series DC MOSFET SSR / `84137860` | 116.39 USD | 20 | QUALIFICATION_CANDIDATE | [제품/검색 결과](https://www.digikey.com/en/products/detail/sensata-crydom/84137860/1816877) |
| ELE-HTR-HS | DigiKey | Three-single-SSR DIN or panel heat sink / `HS103DR` | 159.18 USD | 102 | QUALIFICATION_CANDIDATE | [제품/검색 결과](https://www.digikey.com/en/products/detail/sensata-crydom/HS103DR/2120202) |
| CTL-ENC-001 | DigiKey | 500 by 400 by 210 mm mild-steel enclosure with mounting plate / `MAS0405021R5` | 457.76 USD | 8 | QUALIFICATION_CANDIDATE | [제품/검색 결과](https://www.digikey.com/en/products/detail/hoffman-enclosures-inc/MAS0405021R5/18633327) |

## 해석 규칙

- DigiKey KRW 단가는 제품 페이지의 1개 가격이다. 60,000 KRW 미만 주문의 20,000 KRW 배송비와 수령 시 관세·세금 가능성은 개별 행 가격에 포함하지 않았다.
- 디바이스마트 값은 VAT 포함 표시가를 사용했다. 66,000 KRW 미만 기본 배송 2,700 KRW 및 해외구매/반품 제한은 checkout 전 다시 확인한다.
- AliExpress 4개 검색 결과(5개 BOM evidence 행)는 Playwright Chromium으로 직접 읽었다. 배송·세금·seller·variant·정품 여부가 확정되지 않아 모두 `SAMPLE_ONLY`이고 planning primary로 선택하지 않았다.
- E-stop, safety relay, guard switch, thermal fuse, heater driver, pressure relief/센서는 AliExpress 구매 금지다. 승인 유통망의 datasheet와 추적 가능한 MPN이 필요하다.
- `PARTIAL_ASSEMBLY`는 BOM 행의 일부만 가격이 잡힌 경우다. 예를 들어 D4NS switch body 가격에는 actuator와 cable이 없다.
- `REJECTED`인 CKRD2420은 24~280 VAC 출력 SSR이므로 24 VDC heater driver로 쓰지 않는다.

가격·재고는 변동 가능하며 주문 직전에 재조회한다. 사용자 승인 없이 장바구니·주문·견적 발주를 수행하지 않는다.
