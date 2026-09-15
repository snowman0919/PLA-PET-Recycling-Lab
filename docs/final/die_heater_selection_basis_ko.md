# TH-DIE-01 다이 카트리지 히터 선정 근거

상태: `DIGITAL_INTERFACE_RELEASED / CUSTOM_QUOTE_AND_DRAWING_REQUIRED / PHYSICAL_NOT_RUN`

## 결정

`TH-DIE-01`은 Tempco Hi-Density Metric 맞춤품으로 지정한다. 공개 카탈로그는
주문 가능한 옵션군의 근거이며, 아직 제조사 견적·승인도면·고유 part number를
받지 않았으므로 구매품 확정이나 가열 승인이 아니다. 일반 Ø6 3D-printer
카트리지는 대체품이 아니다.

| 항목 | 계약 사양 |
|---|---|
| 전기 | 24 VDC, 60 W, 2.50 A, 냉간 명목 9.60 Ω |
| 저항 수령 한계 | 20 ±2 °C에서 9.12–10.56 Ω(-5/+10%) |
| sheath | 321 stainless, nominal Ø6.50 mm |
| 외경 | Type CG centerless ground, Ø6.500 ±0.013 mm |
| 삽입 길이 | Type OAL special tolerance, 39.50 ±0.20 mm |
| cold section | lead end ≥9.5 mm, disc end ≥6.4 mm |
| lead | single-ended internal connection, HTL 550 °C lead, ≥300 mm |
| 고정 | Type MFR custom 304SS flange, t1.5 ×20 ×12 mm, 2×Ø3.4 on 14 mm pitch |
| 다이 대응 | Ø6.55 H7 through bore(6.550–6.565 mm), 2×M3-6H depth6 |
| 체결 | SYS-16, 2×M3×8 A4-80 SHCS + Schnorr washer, 1.0 N·m |

Flange는 lead end에서 disc 방향 0.50 ±0.10 mm 위치에 두고, 다이 lead face에
닿았을 때 lead end가 0.40–0.60 mm 밖으로 나오도록 한다. 리드선은 bore 안에
들어가지 않는다. 열간 threadlocker는 쓰지 않고, 냉간 witness mark 후 최초
열사이클이 끝나면 완전히 식힌 상태에서 SYS-16을 재검사한다.

## 공식 근거와 계산

- [Tempco metric Hi-Density 제품/termination 옵션](https://www.tempco.com/Products/Electric-Heaters-and-Elements/Cartridge-Heaters/Hi-Density-Cartridge-Heaters-in-Metric-Sizes.htm): Ø6.5 metric, 321SS sheath, Type CG/OAL/MFR, 고온 lead 옵션.
- [Tempco metric 사양·공차](https://www.tempco.com/Tempco/Resources/Engineering-Data/Specifications-and-Tolerances/Hi-Density-Cartridge-Heater-Metric-Sizes-Specifications-and-Tolerances.htm): 전압·전류, resistance/watt tolerance와 온도·watt-density 한계.
- [Tempco 설치 지침](https://www.tempco.com/Tempco/Resources/02-Cartridge-Resources/HiDensityCartridgeMetricInstall.pdf): reamed close-fit bore, 리드선의 bore 진입 금지, CG 공차와 anti-seize 적용 범위.
- [Tempco metric catalog](https://www.tempco.com/Tempco/Resources/02-Cartridge-Resources/HiDensityCartridgeMetricCatalogPages.pdf): 표준 cold section과 watt-density 식.

외경 한계 6.487–6.513 mm와 bore 한계 6.550–6.565 mm의 opposite-limit 계산은
diametral clearance 0.037–0.078 mm, radial clearance 0.0185–0.0390 mm다.
보수적 heated length는 `39.5−9.5−6.4=23.6 mm`, watt density는
`60/[π×0.65 cm×2.36 cm]=12.45 W/cm²`다. 공개 최대 범위 아래지만 제조사가
265 °C die, 지정 fit, voltage/power 조합을 승인도면에서 확인해야 한다.

## 기각안

[MISUMI E-MHK D5/L30/24 V/60 W](https://sg.misumi-ec.com/vona2/detail/110311245419/)는
lead 절연 자체는 300 °C급이지만 lead outlet을 130 °C 미만으로 유지해야 한다.
현재 die surface 상한 265 °C에서 별도 검증된 냉각 없이 이 조건을 보장할 수
없으므로 채택하지 않는다.

## 구매·수령·물리 gate

제조사는 주문 전에 24 V/60 W, CG/OAL/HTL/MFR 전체와 265 °C 주변조건을
승인도면으로 확인하고 OD/camber, resistance, insulation-resistance 및 hipot
성적서 제공 여부를 회신해야 한다. 수령 후 치수·저항·절연과 무가압 손삽입을
검사한다. anti-seize는 sheath에만 얇게 바르고 리드에는 묻히지 않는다.
사용자 구매 승인, branch fuse/thermal fuse, 냉간 전기검사와 단계적 열시험
전에는 전원을 연결하지 않는다.
