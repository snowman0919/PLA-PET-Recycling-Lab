# ADR-010: 공랭·dual-view gauge·puller·dancer spooler

상태: Accepted for proof — 물리 coupon 전 생산 승인 아님

## 맥락

Ø3 mm die에서 나온 strand를 1.75 mm로 draw down하고 200 g/h 이상에서 PLA/PET를 각각 냉각해야 한다. 직경은 X/Y 두 축으로 측정하며, spooler 장력이 직경제어에 들어오면 안 된다. 일반 1 kg spool 치수는 단일 표준이 아니므로 adapter와 최대 envelope가 필요하다.

## 결정

Die 뒤에는 440 mm 폐쇄형 3-zone cross-flow air tunnel을 둔다. 1.75 mm 원통 radial finite-volume model에서 명목 200 g/h는 평균 공기속도 2.5 m/s, 250 g/h high-flow는 4.0 m/s를 요구한다. 물통은 누수·건조 PET 재흡습·전기 분리와 청소 BOM을 늘리므로 기준형에서 제외한다. Instrumented strand coupon이 PLA 중심 50 °C/PET 70 °C 이하를 tunnel 안에서 입증하지 못할 때만 접지 금속 drip tray와 전기부에서 분리된 짧은 폐쇄 수조를 change request로 평가한다.

Gauge 중심은 die에서 470 mm 떨어뜨린다. Raspberry Pi Camera Module 3 standard, 교체 가능한 close-up optic, 두 방향 backlight와 45° front-surface mirror를 사용해 한 frame에서 `d_x`, `d_y`를 얻는다. Camera Module 3는 제조사 문서상 4608×2592, standard horizontal FOV 66°, 초점범위 약 100 mm 이상이다. Native 100 mm 배치에서도 1.75 mm가 약 62 px이지만 pixel scale만으로 정확도를 주장하지 않는다. 32 mm calibrated field 목표의 close-up optic이 U95≤0.020 mm를 달성하지 못하면 Raspberry Pi HQ/M12 optics로 교체한다. [Raspberry Pi camera documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)

Puller는 Ø40×16 mm 동기구동 nip roller 두 개, 조절식 3–15 N nip, drive encoder와 저하중 Ø30 mm filament odometer를 사용한다. Diameter loop는 spool motor가 아니라 puller 속도를 명령한다. PLA 명목 선속은 약 1.12 m/min이고 die-to-gauge transport delay는 약 25 s이므로 100 Hz roller speed inner loop 위에 1 Hz mass-flow feed-forward + bounded Smith/filtered-PI diameter loop를 둔다. Screw speed는 puller command가 범위를 장시간 벗어날 때만 더 느린 outer loop로 보정한다.

Spooler는 puller 뒤 dancer로 분리한다. 120 mm dancer, 절대각 센서, 0.5 N 목표장력과 0.25 N·m mechanical/electrical torque limit를 사용한다. Spool motor는 dancer 중심을 유지하고, traverse는 spool 회전당 1.80 mm 이동하여 70 mm 범위에서 home/end reversal한다. Holder는 Ø200×73 mm까지 받고 Ø80 mm 이상 core에 교환 adapter를 사용한다. Bambu의 1 kg 제품 TDS는 Ø200×67 mm spool을 명시하고, eSUN eBOX 공식 제품 자료의 최대 envelope는 Ø200×73 mm다. [Bambu filament TDS](https://cdn.shopify.com/s/files/1/0584/7236/6216/files/Bambu_PLA-CF_Technical_Data_Sheet_V3.pdf), [eSUN eBOX product data](https://www.esun3d.com/ebox-product/)

## 근거와 gate

NatureWorks 자료의 PLA density 1.24와 Tg 55–60 °C를 바탕으로 PLA puller 중심온도를 50 °C로 제한한다. PET proof에는 supplier PET의 density 1.39와 GEHR PET 자료의 Tg 81.5 °C보다 낮은 70 °C 중심온도 gate를 사용한다. 열전도율·비열은 sensitivity assumption이므로 실제 lot 결과로 갱신한다. [NatureWorks Ingeo grade brochure](https://www.natureworksllc.com/~/media/Technical_Resources/one-pagers/ingeo-resin-grades-brochure_pdf), [GEHR PET TDS](https://en.gehr.de/wp-content/uploads/2022/03/GEHR-PET_Technical-data-sheet.pdf)

광학 U95, mirror 두 축 scale, contamination detection, 실제 cross-flow, center/roller temperature, puller slip, dancer tension과 full-spool traverse가 물리시험으로 통과하기 전 ±0.05 mm 생산 성능을 주장하지 않는다. Sorter 또는 shredder 진동이 gauge frame에서 0.05 g RMS 미만으로 입증되지 않으면 extrusion/gauge phase와 시간적으로 분리한다.
