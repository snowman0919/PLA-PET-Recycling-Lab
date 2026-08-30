within PLA_PET_Recycler.Components;
model PhaseGearMesh
  parameter Real stiffness=2200 "N.m/rad";
  parameter Real damping=1.5 "N.m.s/rad";
  parameter Real backlash=0.006 "rad total";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a rightShaft;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b leftShaft;
  Modelica.Mechanics.Rotational.Components.IdealGear counterRotation(ratio=-1,useSupport=false);
  SmoothBacklash compliance(stiffness=stiffness,damping=damping,backlash=backlash);
  Real phaseError;
  Real meshTorque;
  Real separatingForce;
equation
  connect(rightShaft,counterRotation.flange_a);
  connect(counterRotation.flange_b,compliance.flangeA);
  connect(compliance.flangeB,leftShaft);
  phaseError=rightShaft.phi+leftShaft.phi;
  meshTorque=-leftShaft.tau;
  separatingForce=abs(meshTorque)/Generated.CADParameters.phaseGearRadius*tan(Modelica.Constants.pi/9);
end PhaseGearMesh;
