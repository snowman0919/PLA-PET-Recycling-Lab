# 열·전력·forming screening

24 V 600 W PSU에서 normal-state limit는 500 W이고 최소 reserve는 100 W다. SHREDDING/PREHEATING/EXTRUSION/COOLDOWN의 peak는 각각 477.0/405.0/490.0/61.0 W이며 모두 phase limit를 만족한다. Shredder와 heater/screw는 상호배제한다.

`cooling_matrix.csv`는 PLA/PET, 50/75/100/125/150/175/200 g/h, fan 40/70/100%, duct 2.0/3.5/5.0 m/s를 모두 계산한다. 200 g/h에서 coupled forming 기준을 만족하지 않는 조합은 `DIGITAL_STRETCH_TARGET`이며 실제 filament tolerance를 주장하지 않는다.

EX-DIE-04의 두 10×2.5×1.5 mm 304 stainless bending web은 265 °C 보수 항복강도 150 MPa와 insert annular projected area를 쓴 first-yield screening에서 4.32 MPa다. 목표 3–6 MPa 안이지만 large deflection·마찰·열화가 빠져 있으므로 동일 lot 3개 고온 물리 coupon 전에는 relief 합격값이 아니다.

PET predry는 `UNQUALIFIED_EXTERNAL_PROCESS`; 65 °C/7 h를 qualified recipe로 주장하지 않는다.
