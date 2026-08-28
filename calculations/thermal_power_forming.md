# 열·전력·forming screening

24 V 600 W PSU에서 동시 peak 합은 862.0 W이므로 허용하지 않는다. Hardware/state arbiter는 500.0 W, margin 100.0 W이며 shredder와 heater/screw는 상호배제한다.

`cooling_matrix.csv`는 PLA/PET, 50/100/150/200 g/h, fan 40/70/100%, duct 2.0/3.5/5.0 m/s를 모두 계산한다. 200 g/h에서 요구 h가 실측되지 않았으므로 risk가 남는 조합은 virtual requirement이며 puller-entry thermocouple 없이는 합격이 아니다.

PET predry는 `UNQUALIFIED_EXTERNAL_PROCESS`; 65 °C/7 h를 qualified recipe로 주장하지 않는다.
