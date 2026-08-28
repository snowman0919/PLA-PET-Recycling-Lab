within PLA_PET_Recycler.Components;
model FrameMount
  input Real processReaction;
  output Real baseReaction;
  output Real tippingMoment;
  output Real anchorTension;
  inner Modelica.Mechanics.MultiBody.World world(enableAnimation=false);
  Modelica.Mechanics.MultiBody.Parts.FixedTranslation datumToCOM(
    r=Generated.CADParameters.assemblyCOM,animation=false);
  Modelica.Mechanics.MultiBody.Parts.Body assemblyBody(
    m=Generated.CADParameters.assemblyMass,r_CM={0,0,0},
    I_11=Generated.CADParameters.assemblyInertia[1,1],
    I_22=Generated.CADParameters.assemblyInertia[2,2],
    I_33=Generated.CADParameters.assemblyInertia[3,3],
    I_21=Generated.CADParameters.assemblyInertia[2,1],
    I_31=Generated.CADParameters.assemblyInertia[3,1],
    I_32=Generated.CADParameters.assemblyInertia[3,2],animation=false);
  Modelica.Mechanics.MultiBody.Forces.SpringDamperParallel mountCompliance(
    c=1.0e6,d=1.0e4,
    s_unstretched=sqrt(sum(Generated.CADParameters.assemblyCOM[i]^2 for i in 1:3)));
equation
  connect(world.frame_b,datumToCOM.frame_a);
  connect(datumToCOM.frame_b,assemblyBody.frame_a);
  connect(world.frame_b,mountCompliance.frame_a);
  connect(datumToCOM.frame_b,mountCompliance.frame_b);
  baseReaction=Generated.CADParameters.assemblyMass*Modelica.Constants.g_n+processReaction;
  tippingMoment=abs(processReaction)*0.59;
  anchorTension=max(0,tippingMoment/0.45-Generated.CADParameters.assemblyMass*Modelica.Constants.g_n/2);
end FrameMount;
