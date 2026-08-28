within PLA_PET_Recycler.Components;
model PhaseGearPair
  parameter Real stiffness = 2200 "N.m/rad";
  parameter Real damping = 1.5 "N.m.s/rad";
  parameter Real backlash = 0.006 "rad total";
  input Real rightAngle;
  input Real leftAngle;
  output Real phaseError;
  output Real meshTorque;
  output Real separatingForce;
equation
  phaseError = rightAngle + leftAngle;
  meshTorque = if abs(phaseError)<=backlash/2 then 0 else stiffness*(phaseError-sign(phaseError)*backlash/2)+damping*der(phaseError);
  separatingForce = abs(meshTorque)/Generated.CADParameters.phaseGearRadius*tan(Modelica.Constants.pi/9);
end PhaseGearPair;
