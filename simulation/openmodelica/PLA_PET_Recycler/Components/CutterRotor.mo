within PLA_PET_Recycler.Components;
model CutterRotor
  parameter Real J = Generated.CADParameters.cutterRotorJ;
  parameter Real viscousFriction = 0.05;
  input Real driveTorque;
  input Real loadTorque;
  output Real angle;
  output Real speed;
  Modelica.Mechanics.Rotational.Components.Inertia rotor(
    J=J, phi(start=0,fixed=true), w(start=0,fixed=true));
  Modelica.Mechanics.Rotational.Components.Damper bearingLoss(d=viscousFriction);
  Modelica.Mechanics.Rotational.Components.Fixed support;
  Modelica.Mechanics.Rotational.Sources.Torque driveSource(useSupport=false);
  Modelica.Mechanics.Rotational.Sources.Torque loadSource(useSupport=false);
equation
  driveSource.tau=driveTorque;
  loadSource.tau=-loadTorque;
  connect(driveSource.flange,rotor.flange_a);
  connect(loadSource.flange,rotor.flange_b);
  connect(rotor.flange_b,bearingLoss.flange_a);
  connect(bearingLoss.flange_b,support.flange);
  angle=rotor.phi;
  speed=rotor.w;
end CutterRotor;
