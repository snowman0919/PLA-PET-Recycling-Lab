# 제어함 실배치 후보와 근거

조회일: 2026-08-28. 상태: `EXACT_MPN ENVELOPE / QUALIFICATION HOLD / NO PURCHASE AUTHORIZED`.

이 문서는 `bom.csv`, `cost_evidence.csv`, `cad/parameters/baseline.json` 사이의 치수·수량 연결을 설명한다. 노란색 FreeCAD 객체는 실제 MPN 외형이지만 부하·열·차단·기능안전 검증이 끝난 selected hardware가 아니다.

| Ref / Part ID | 수량 | 실제 후보와 패널 외형 | 공식 기술 근거 | 가격·재고 근거 | 남은 gate |
|---|---:|---|---|---|---|
| ENC1 / CTL-ENC-001 | 1 | nVent HOFFMAN `MAS0405021R5`, 500×400×210 mm, plate 450×370 mm | [nVent MAS catalog](https://www.nvent.com/sites/default/files/acquiadam/assets/Product_Catalogue_nVent_Hoffman_ENG_02_WM.pdf) | [DigiKey](https://www.digikey.com/en/products/detail/hoffman-enclosures-inc/MAS0405021R5/18633327), 457.76 USD, stock 8 | SCCR, gland, 열상승, PE와 panel-shop 승인 |
| K2A/K2B / SAF-CON-001 | 2 | ABB `AFS30-30-22-11`, 각 45×119.5×86 mm | [ABB AFS safety contactor catalog](https://library.e.abb.com/public/2d45de99b0b5488d8355b6d32273527e/1SBC100208C0203_Catalogue%20AF%20safety%20Contactors.pdf) | [Mouser](https://www.mouser.com/en/ProductDetail/ABB/AFS30-30-22-11?qs=iLKYxzqNS76HP0X0B0esXA%3D%3D), 316.39 USD/개, stock 1 | 두 zone의 실측전류, DC-1 pole 직렬구성, coil/output 정합, series EDM fault test |
| FBR01…FBR14 / SAF-FUS-HLD | 14 | Eaton Bussmann `CHCC1DU`, 각 17.5×73.88×83.19 mm | [Eaton CHCC datasheet](https://www.eaton.com/content/dam/eaton/products/electrical-circuit-protection/fuses/data-sheets/bus-ele-ds-10430-chcc-chm-chpv.pdf) | [DigiKey](https://www.digikey.com/en/products/detail/eaton-bussmann-electrical-division/CHCC1DU/2767773), 95.10 USD/개, stock 0 | holder만 배치됨; main holder와 fuse link 정격·차단용량·coordination은 placeholder |
| QH1…QH6 / ELE-HTR-DRV | 6 | Sensata Crydom `84137860`, 패널 회전 외형 각 60.2×35.05×44.45 mm | [Sensata GN datasheet](https://www.sensata.com/sites/default/files/a/sensata-gn-series-dc-output-panel-mount-ssr-datasheet.pdf) | [DigiKey](https://www.digikey.com/en/products/detail/sensata-crydom/84137860/1816877), 116.39 USD/개, stock 20 | 40 °C derating, default-off, welded-on, terminal과 branch-fuse 시험 |
| HS1/HS2 / ELE-HTR-HS | 2 | Sensata Crydom `HS103DR`, 각 76.2×60.2×132.1 mm | [Sensata HS103 datasheet](https://www.sensata.com/sites/default/files/a/sensata-hs103-series-heat-sink-datasheet.pdf) | [DigiKey](https://www.digikey.com/en/products/detail/sensata-crydom/HS103DR/2120202), 159.18 USD/개, stock 102 | 각 방열판의 SSR 3개 합산손실, interface material, 방향과 함내 온도상승 |

## 패널 수량 논리

14개 branch-holder 자리는 always-on logic 1, Tower A shredder/sorter 2, Tower B extruder drive 1, puller/spooler 1, dryer blower·agitator·feeder 1, desiccant 1, cooling fan 1, extruder heater 4, PLA/PET dryer heater 2로 예약했다. 이는 holder 자리 수를 정한 것이며 fuse ampere 선정이 아니다. PSU label, source fault-current와 각 branch peak가 확인되기 전 `FMAIN_FLINKS`는 주황색 placeholder로 남는다.

K2A는 Tower A 위험 motion, K2B는 Tower B drive/heater를 차단한다. 두 mirror NC 접점은 safety-relay EDM/reset feedback에 직렬 연결한다. `24 V × 25 A` nominal 산술이나 480 W software ceiling을 접촉기·퓨즈·전선 선정값으로 사용하지 않는다.

## CAD 상태 구분

- 녹색: planning-selected candidate envelope. 주문 승인은 아님.
- 노란색: 정확한 MPN과 수량을 배치한 qualification/sizing candidate.
- 파란색: 190×130 mm PCB fabrication-HOLD와 사용자 보유 보드 실측 대기 영역.
- 주황색: exact MPN이 없어 주문·드릴 가공에 사용할 수 없는 placeholder.
- 빨강/노랑/파랑/초록 duct: 고전류·hardwired safety·logic/sensor·PE 전선 경로 예약.
- 자홍색: 단자 접근과 service keep-out.
