within PLA_PET_Recycler.Components;
model CutterLoadSurrogate
  parameter Integer mode = 1 "0 no-load, 1 PLA, 2 PET, 3 impact, 4 multi, 5 backlash";
  parameter Real jamStart = 1e9;
  parameter Real forcedLoad = 0;
  output Real torque;
equation
  torque = forcedLoad + (if time>=jamStart then 30 else 0) +
    (if mode==0 then 0.8 else if mode==1 then 5+2.5*max(0,sin(2*Modelica.Constants.pi*7*time))
     else if mode==2 then 6+3.2*max(0,sin(2*Modelica.Constants.pi*5*time))
     else if mode==3 then 4+16*exp(-((time-2)/0.035)^2)
     else if mode==4 then 6+17*exp(-((time-2)/0.09)^2)
     else 4+12*exp(-((time-0.25)/0.02)^2));
end CutterLoadSurrogate;
