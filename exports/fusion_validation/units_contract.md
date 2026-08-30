# 단위 계약

STEP 형상은 mm, 해석 입력은 mm·N·N·mm·MPa·°C·s 체계다. JSON key에 `_nm`가 붙은 torque만 Fusion 입력 전 `×1000`하여 N·mm로 변환한다. 압력 `_mpa`는 MPa, 질량 `_kg`는 kg, 중력은 m/s²다. 결과 CSV의 단위 열은 비울 수 없으며 Pa와 MPa, m와 mm의 묵시 변환을 금지한다.
