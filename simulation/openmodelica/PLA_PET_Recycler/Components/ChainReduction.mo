within PLA_PET_Recycler.Components;
model ChainReduction
  parameter Real ratio = 2.0;
  parameter Real efficiency = 0.90;
  parameter Real pitchRadius = Generated.CADParameters.cutterSprocketRadius;
  parameter Real stiffness = 1800 "N.m/rad cutter-equivalent";
  parameter Real damping = 1.2 "N.m.s/rad";
  parameter Real backlash = 0.008 "rad at cutter";
  input Real motorTorque;
  input Real motorAngle;
  input Real cutterAngle;
  output Real cutterTorque;
  output Real kinematicCutterAngle;
  output Real elasticTorque;
  output Real tightSideForce;
  Modelica.Mechanics.Rotational.Sources.Position motorPosition(exact=true,useSupport=false);
  Modelica.Mechanics.Rotational.Sources.Position cutterPosition(exact=true,useSupport=false);
  Modelica.Mechanics.Rotational.Components.IdealGear reduction(ratio=ratio,useSupport=false);
  Modelica.Mechanics.Rotational.Components.ElastoBacklash chainElasticity(
    c=stiffness,d=damping,b=backlash);
equation
  motorPosition.phi_ref=motorAngle;
  cutterPosition.phi_ref=cutterAngle;
  connect(motorPosition.flange,reduction.flange_a);
  connect(reduction.flange_b,chainElasticity.flange_a);
  connect(chainElasticity.flange_b,cutterPosition.flange);
  cutterTorque = motorTorque*ratio*efficiency;
  kinematicCutterAngle = motorAngle/ratio;
  elasticTorque=chainElasticity.flange_b.tau;
  tightSideForce = abs(cutterTorque)/pitchRadius;
end ChainReduction;
