within PLA_PET_Recycler.Components;
model FilamentSpan
  parameter Real stiffness=55 "N/m";
  parameter Real damping=2 "N.s/m";
  input Real pullerSpeed;
  input Real spoolSurfaceSpeed;
  output Real extension(start=0.02,fixed=true);
  output Real tension;
equation
  der(extension)=pullerSpeed-spoolSurfaceSpeed;
  tension=max(0,stiffness*extension+damping*(pullerSpeed-spoolSurfaceSpeed));
end FilamentSpan;
