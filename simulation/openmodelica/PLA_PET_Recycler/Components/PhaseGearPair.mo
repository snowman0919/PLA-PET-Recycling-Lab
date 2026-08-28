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
  Modelica.Mechanics.Rotational.Sources.Position rightPosition(exact=true,useSupport=false);
  Modelica.Mechanics.Rotational.Sources.Position leftPosition(exact=true,useSupport=false);
  Modelica.Mechanics.Rotational.Components.IdealGear counterRotation(ratio=-1,useSupport=false);
  Modelica.Mechanics.Rotational.Components.ElastoBacklash meshCompliance(
    c=stiffness,d=damping,b=backlash);
equation
  rightPosition.phi_ref=rightAngle;
  leftPosition.phi_ref=leftAngle;
  connect(rightPosition.flange,counterRotation.flange_a);
  connect(counterRotation.flange_b,meshCompliance.flange_a);
  connect(meshCompliance.flange_b,leftPosition.flange);
  phaseError = rightAngle + leftAngle;
  meshTorque = meshCompliance.flange_b.tau;
  separatingForce = abs(meshTorque)/Generated.CADParameters.phaseGearRadius*tan(Modelica.Constants.pi/9);
end PhaseGearPair;
