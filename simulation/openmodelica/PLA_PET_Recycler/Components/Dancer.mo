within PLA_PET_Recycler.Components;
model Dancer
  parameter Real J=0.004;
  input Real lineTension;
  output Real angle;
  Real angularVelocity;
  inner Modelica.Mechanics.MultiBody.World world(g=0,enableAnimation=false);
  Modelica.Mechanics.MultiBody.Joints.Revolute pivot(
    n={0,1,0},useAxisFlange=true,phi(start=0.35,fixed=true),w(start=0,fixed=true));
  Modelica.Mechanics.MultiBody.Parts.FixedTranslation arm(r={0.105,0,0},animation=false);
  Modelica.Mechanics.MultiBody.Parts.Body dancerMass(
    m=0.18,r_CM={-0.0525,0,0},I_11=0.0002,I_22=J,I_33=J,animation=false);
  Modelica.Mechanics.Rotational.Components.Fixed support;
  Modelica.Mechanics.Rotational.Components.SpringDamper restoring(
    c=0.6,d=0.08,phi_rel0=0.35);
  Modelica.Mechanics.Rotational.Sources.Torque filamentTorque(useSupport=false);
equation
  filamentTorque.tau=0.105*lineTension;
  connect(world.frame_b,pivot.frame_a);
  connect(pivot.frame_b,arm.frame_a);
  connect(arm.frame_b,dancerMass.frame_a);
  connect(support.flange,restoring.flange_a);
  connect(restoring.flange_b,pivot.axis);
  connect(filamentTorque.flange,pivot.axis);
  angle=pivot.phi;
  angularVelocity=pivot.w;
end Dancer;
