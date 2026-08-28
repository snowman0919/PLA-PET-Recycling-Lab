within PLA_PET_Recycler.Components;
model CutterRotor
  parameter Real J = Generated.CADParameters.cutterRotorJ;
  parameter Real viscousFriction = 0.05;
  input Real driveTorque;
  input Real loadTorque;
  output Real angle(start=0,fixed=true);
  output Real speed(start=0,fixed=true);
equation
  der(angle)=speed;
  J*der(speed)=driveTorque-loadTorque-viscousFriction*speed;
end CutterRotor;
