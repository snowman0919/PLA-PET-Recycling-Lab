within PLA_PET_Recycler.Components;
model FilamentSpan
  parameter Real stiffness=55 "N/m";
  parameter Real damping=2 "N.s/m";
  input Real pullerSpeed;
  input Real spoolSurfaceSpeed;
  output Real extension;
  output Real tension;
  Real pullerPosition(start=0,fixed=true);
  Real spoolPosition(start=0,fixed=true);
  Modelica.Mechanics.Translational.Sources.Position pullerMotion(exact=true,useSupport=false);
  Modelica.Mechanics.Translational.Sources.Position spoolMotion(exact=true,useSupport=false);
  Modelica.Mechanics.Translational.Components.SpringDamper filament(c=stiffness,d=damping,s_rel0=0);
equation
  der(pullerPosition)=pullerSpeed;
  der(spoolPosition)=spoolSurfaceSpeed;
  pullerMotion.s_ref=pullerPosition+0.02;
  spoolMotion.s_ref=spoolPosition;
  connect(spoolMotion.flange,filament.flange_a);
  connect(pullerMotion.flange,filament.flange_b);
  extension=filament.s_rel;
  tension=max(0,filament.f);
end FilamentSpan;
