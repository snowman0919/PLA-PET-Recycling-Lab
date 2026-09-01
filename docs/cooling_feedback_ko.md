# Cooling feedback topology와 한계

선택 topology는 `A4 branch current + fan1/fan2 tach through 2:1 mux(A14 PCINT22)`다. fan 1 stopped, fan 2 stopped, both stopped, command/no feedback, command-off implausible tach를 구분한다. 한 팬 손실도 forming-chain fault가 된다.

전류는 electrical load, tach는 rotation만 증명한다. duct blockage/filter fouling/leakage/strand position은 실제 airflow가 아니며 `analysis/process_risk/cooling_airflow_sensitivity.*`의 inferred range로만 다룬다. 물리 anemometer/pressure coupon 전에는 airflow measured를 주장하지 않는다.
