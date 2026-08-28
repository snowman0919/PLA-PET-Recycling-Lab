within PLA_PET_Recycler.Components;
model FrameMount
  input Real processReaction;
  output Real baseReaction;
  output Real tippingMoment;
  output Real anchorTension;
equation
  baseReaction=Generated.CADParameters.assemblyMass*Modelica.Constants.g_n+processReaction;
  tippingMoment=abs(processReaction)*0.59;
  anchorTension=max(0,tippingMoment/0.45-Generated.CADParameters.assemblyMass*Modelica.Constants.g_n/2);
end FrameMount;
