# Chiron 기반 마감 판정

설계 목표는 낭비된 PLA/PET를 재활용하는 compact 공용 경로다. 고토크 cycloidal-inspired 양축 분쇄 구조를 유지한다. 이번 마감에서 새로운 고온spring,카메라/Pi,대형건조기,AC PTC 별도제어를 필수 BOM으로 추가하지 않는다.

## 이번에 확정한 선택
- donor: Anycubic Chiron 1대. 프로파일과24 V800 W PSU도 동일 자산이다.
- frame:2020 기본/2040 기존국부보강 유지. 재고 길이에 맞춘 cut plan은 실제 길이 확보 후 확정한다.
- print: 기존12종은PLA9종/ABS3종으로 유지. 신규외장은PLA. 작은 ABS부품만209.11 g,예비100 g을 남긴다.
- power:800 W 보고값은 자산기록이며500 W 제어한도와분쇄/가열상호배제는그대로다.
- heat: 공용PET/PLA 경로는24 V 제어 가열기. 220 V245 C PTC는예비품이며전력스위칭/단자BOM을추가하지않는다.
- CNC: 절삭/압력/정밀접합부만국부가공. 평판과가드는절단/드릴/절곡,도너축과가이드는재사용한다.

## 제작도면 동결 전 남은 입력
sourcing/minimum_confirmation_bom.csv의재고확인을먼저받는다. 미확인을전부신규구매로채우지않는다. 특히감속모터출력축/장착면,히터OD/길이,도너driver신호와프로파일유효길이가실제어댑터치수를결정한다. 기존puller/spooler의PWM/DIR와도너stepper의STEP/DIR차이는소프트웨어어댑터수정으로검증해야하며사진확인전에호환완료로표시하지않는다.

이전진행에서발견한후방고온datum/collar간극과중심정렬은아직실제수정이필요하다. 이문서또는추가800 W여유로해당문제를PASS로바꾸지않는다. 반면선택하지않은HS-R1-S2의1,222 MPa시험조건은본체마감의필수조건이아니다.

## 산출물의 현재 의미
build_plan.py와resource_budget.py를실행해기존부품의재질/전력/수량을정합시켰다. 기존STL/3MF/STEP36개해시를확인했으며이번에새형상이나slicer결과를만들었다는주장은없다. CAD강도검증이나전체119행BOM의재생성완료도아니다.

현재상태는 DESIGN_BASIS_LOCKED_INTERFACE_CHECKS_OPEN이다. 실제구매수량과핵심접합치수가정해지고남은국부수정이끝나야 FABRICATION_PACKAGE_READY로승격한다. 가격과공급처의최종값이없으면0원견적으로채우지않는다. 관련변경은범위를나눠검증후커밋하며원격push/merge/발주는별도로보고한다.
