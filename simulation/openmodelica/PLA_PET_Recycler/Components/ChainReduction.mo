within PLA_PET_Recycler.Components;
model ChainReduction
  parameter Real ratio = 2.0;
  parameter Real efficiency = 0.90;
  parameter Real pitchRadius = Generated.CADParameters.cutterSprocketRadius;
  input Real motorTorque;
  input Real motorAngle;
  output Real cutterTorque;
  output Real cutterAngle;
  output Real tightSideForce;
equation
  cutterTorque = motorTorque*ratio*efficiency;
  cutterAngle = motorAngle/ratio;
  tightSideForce = abs(cutterTorque)/pitchRadius;
end ChainReduction;
