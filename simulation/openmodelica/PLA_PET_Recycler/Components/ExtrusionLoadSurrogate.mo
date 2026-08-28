within PLA_PET_Recycler.Components;
model ExtrusionLoadSurrogate
  parameter Real jamStart = 1e9;
  parameter Real pressureFinal = 3e6;
  output Real pressure;
  output Real torque;
equation
  pressure = pressureFinal*(1-exp(-time/1.5)) + (if time>=jamStart then 12e6 else 0);
  torque = 2.5 + 1.8e-6*pressure;
end ExtrusionLoadSurrogate;
