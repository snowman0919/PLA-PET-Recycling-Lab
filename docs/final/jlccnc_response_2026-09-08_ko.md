# JLCCNC SCM440 스크루·배럴 능력 문의 회신 판정

- 회신자: `effie@jlcpcb.com`
- 회신 시각: 2026-09-07 19:07:46 -0700 (한국 시각 2026-09-08)
- 원본 EML SHA-256: `bdb5cedc2f51be47eaf15719a226b4ad6ecb442ab823eb5fbf558409d3e2daf7`
- 메일 인증: DKIM/SPF/DMARC `pass`
- 사용자 확인: 문의 발송 및 회신 수신
- 주문·결제·생산 승인: `NO`

## 공급자 답변의 설계 판정

| 요구사항 | 회신 | 판정 |
|---|---|---|
| 추적 가능한 SCM440/JIS G 4105 및 MTC | 공식 웹사이트 목록 재료만 지원하며 비목록 재료 조달 불가 | `REJECTED_FOR_CURRENT_SPEC` |
| Q&T 28–32 HRC | 열처리 미제공 | `REJECTED_FOR_CURRENT_SPEC` |
| 가스질화, 유효 경화층·경도·화합물층 | 가스질화 미제공, 관련 보증 불가 | `REJECTED_FOR_CURRENT_SPEC` |
| 질화 후 호닝/연삭과 245–270 °C 최종 물성 | 공개된 표면처리만 지원; 지정 최종 상태 자체를 제공하지 않음 | `REJECTED_FOR_CURRENT_SPEC` |
| 치수·공차·검사 성적서 | STEP/STP와 CNC Remark 제출 후 개별 심사; 일반 최저 공차 ±0.05 mm | `HOLD` |
| 동일 heat/process coupon 선승인 후 본품 진행 | 한 주문 안의 coupon-first 승인 순서 미지원 | `REJECTED_FOR_CURRENT_SEQUENCE` |

## 결론과 다음 gate

JLCCNC는 현 `EX-SCR-01`/`EX-BAR-01`의 완결 공급처로 채택하지 않는다. 특히 배럴
보어 `+0.02/0 mm`, 스크루 외경 `-0.02/0 mm`, TIR `≤0.05/256 mm`는 일반 ±0.05 mm
능력 문구만으로 승인할 수 없다. JLCCNC의 무료 STEP 심사는 공개 능력 밖 요구를
충족한다는 증거가 아니며, 사용자가 별도 승인하지 않은 재료 대체도 허용하지 않는다.

다음 공급업체는 추적 가능한 SCM440, Q&T, 가스질화, 질화 후 최종 호닝/연삭,
동일 heat/process coupon 선승인, datum 기반 최종검사, 245–270 °C 물성 제공 또는
그 부재의 명시를 한 공정 책임 아래 수락해야 한다. 이 업체가 정해질 때까지 hot-zone
재료·열간간극·국부응력 검증과 전체 스크루·배럴 발주는 `HOLD`다.

원본 EML은 개인 메일 라우팅 헤더를 포함하므로 저장소·release ZIP에 복제하지 않고,
위 해시와 판정표만 검토 가능한 증적으로 유지한다.
