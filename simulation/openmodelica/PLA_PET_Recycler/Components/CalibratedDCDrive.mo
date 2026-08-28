within PLA_PET_Recycler.Components;
model CalibratedDCDrive
  parameter Real noLoadCurrent = 1.8 "A reference sensitivity only";
  parameter Real torquePerAmp = 1.35 "N.m/A at motor";
  parameter Real ratio = 2.0;
  parameter Real efficiency = 0.72;
  input Real torqueRequest "N.m at cutter";
  input Boolean enable;
  output Real torque;
  output Real current;
equation
  torque = if enable then max(-22.0,min(22.0,torqueRequest)) else 0;
  current = if enable then noLoadCurrent + abs(torque)/(torquePerAmp*ratio*efficiency) else 0;
end CalibratedDCDrive;
