within PLA_PET_Recycler.Components;
model ElasticChainDrive
  parameter Real ratio=2.5;
  parameter Real efficiency=0.85;
  parameter Real stiffness=1800 "N.m/rad cutter equivalent";
  parameter Real damping=1.2 "N.m.s/rad";
  parameter Real backlash=0.008 "rad";
  parameter Integer cutterTeeth(min=3)=30 "CAD CutterSprocket30T";
  parameter Real chainPitch(min=0)=0.009525 "m; CAD #35 pitch";
  parameter Real cutterPitchRadius=chainPitch/(2*sin(Modelica.Constants.pi/cutterTeeth)) "m";
  parameter Real slackSideTension(min=0)=0 "N; unmeasured, zero is not a qualified preload";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a motorSprocket;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b cutterSprocket;
  LossyGearbox reduction(ratio=ratio,efficiency=efficiency);
  SmoothBacklash elasticity(stiffness=stiffness,damping=damping,backlash=backlash);
  Real transmittedTorque;
  Real tightSideForce;
  Real effectiveChainForce;
  Real shaftRadialForceBound "N; sum of tensions, conservative vector-magnitude bound";
equation
  connect(motorSprocket,reduction.motorSide);
  connect(reduction.outputSide,elasticity.flangeA);
  connect(elasticity.flangeB,cutterSprocket);
  transmittedTorque=-cutterSprocket.tau;
  assert(cutterPitchRadius>0,"Positive chain pitch radius required");
  effectiveChainForce=abs(transmittedTorque)/cutterPitchRadius;
  tightSideForce=effectiveChainForce+slackSideTension;
  shaftRadialForceBound=tightSideForce+slackSideTension;
end ElasticChainDrive;
