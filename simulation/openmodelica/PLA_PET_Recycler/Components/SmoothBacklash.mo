within PLA_PET_Recycler.Components;
model SmoothBacklash
  parameter Real stiffness=1800 "N.m/rad";
  parameter Real damping=1.2 "N.m.s/rad";
  parameter Real backlash=0.008 "rad total";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a flangeA;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flangeB;
  Real relativeAngle;
  Real relativeSpeed;
  Real engagement;
  Real torque;
equation
  relativeAngle=flangeA.phi-flangeB.phi;
  relativeSpeed=der(relativeAngle);
  engagement=(relativeAngle/(0.5*backlash+1e-6))^2/(1+(relativeAngle/(0.5*backlash+1e-6))^2);
  torque=engagement*(stiffness*relativeAngle+damping*relativeSpeed);
  flangeA.tau=torque;
  flangeB.tau=-torque;
end SmoothBacklash;
