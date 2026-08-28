within PLA_PET_Recycler.Components;
model VariableRadiusSpool
  parameter Real fillStart=0;
  input Real lineSpeed;
  input Real dancerAngle;
  output Real fillFraction(start=fillStart,fixed=true);
  output Real radius;
  output Real inertia;
  output Real surfaceSpeed;
equation
  der(fillFraction)=if fillFraction<1 then max(0,lineSpeed)/4200 else 0;
  radius=0.026+(0.100-0.026)*min(1,fillFraction);
  inertia=Generated.CADParameters.spoolEmptyJ+(Generated.CADParameters.spoolFullJ-Generated.CADParameters.spoolEmptyJ)*min(1,fillFraction);
  surfaceSpeed=lineSpeed*(1+0.02*(dancerAngle-0.35)+0.005*sin(2*Modelica.Constants.pi*0.8*time));
end VariableRadiusSpool;
