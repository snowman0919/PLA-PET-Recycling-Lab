within PLA_PET_Recycler.Components;
model ElasticChainDrive
  parameter Real ratio=2.5;
  parameter Real efficiency=0.85;
  parameter Real stiffness=1800 "N.m/rad cutter equivalent";
  parameter Real damping=1.2 "N.m.s/rad";
  parameter Real backlash=0.008 "rad";
  parameter Real cutterPitchRadius=0.03649 "m";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a motorSprocket;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b cutterSprocket;
  LossyGearbox reduction(ratio=ratio,efficiency=efficiency);
  SmoothBacklash elasticity(stiffness=stiffness,damping=damping,backlash=backlash);
  Real transmittedTorque;
  Real tightSideForce;
equation
  connect(motorSprocket,reduction.motorSide);
  connect(reduction.outputSide,elasticity.flangeA);
  connect(elasticity.flangeB,cutterSprocket);
  transmittedTorque=-cutterSprocket.tau;
  tightSideForce=abs(transmittedTorque)/cutterPitchRadius;
end ElasticChainDrive;
