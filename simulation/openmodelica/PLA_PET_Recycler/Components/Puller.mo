within PLA_PET_Recycler.Components;
model Puller
  parameter Real rollerRadius=0.020;
  parameter Real rollerInertia=0.00024;
  parameter Real speedGain=0.08;
  input Real speedCommand;
  input Boolean enable;
  output Real speed;
  Modelica.Mechanics.Rotational.Components.Inertia roller(
    J=rollerInertia, phi(start=0,fixed=true), w(start=0,fixed=true));
  Modelica.Mechanics.Rotational.Components.Damper bearingLoss(d=0.0008);
  Modelica.Mechanics.Rotational.Components.Fixed support;
  Modelica.Mechanics.Rotational.Sources.Torque motor(useSupport=false);
equation
  motor.tau=max(-1.2,min(1.2,speedGain*((if enable then speedCommand else 0)/rollerRadius-roller.w)));
  connect(motor.flange,roller.flange_a);
  connect(roller.flange_b,bearingLoss.flange_a);
  connect(bearingLoss.flange_b,support.flange);
  speed=roller.w*rollerRadius;
end Puller;
