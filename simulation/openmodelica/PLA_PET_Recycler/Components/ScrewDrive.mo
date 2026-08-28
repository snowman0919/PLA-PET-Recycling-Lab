within PLA_PET_Recycler.Components;
model ScrewDrive
  parameter Real J = Generated.CADParameters.screwJ;
  input Real targetSpeed;
  input Real loadTorque;
  input Boolean enable;
  output Real speed;
  output Real motorTorque;
  Modelica.Mechanics.Rotational.Components.Inertia screw(
    J=J, phi(start=0,fixed=true), w(start=0,fixed=true));
  Modelica.Mechanics.Rotational.Components.Damper bearingLoss(d=0.02);
  Modelica.Mechanics.Rotational.Components.Fixed support;
  Modelica.Mechanics.Rotational.Sources.Torque motor(useSupport=false);
  Modelica.Mechanics.Rotational.Sources.Torque processLoad(useSupport=false);
equation
  motorTorque = if enable then max(-22,min(22,1.5*(targetSpeed-speed)+loadTorque)) else 0;
  motor.tau=motorTorque;
  processLoad.tau=-loadTorque;
  connect(motor.flange,screw.flange_a);
  connect(processLoad.flange,screw.flange_b);
  connect(screw.flange_b,bearingLoss.flange_a);
  connect(bearingLoss.flange_b,support.flange);
  speed=screw.w;
end ScrewDrive;
