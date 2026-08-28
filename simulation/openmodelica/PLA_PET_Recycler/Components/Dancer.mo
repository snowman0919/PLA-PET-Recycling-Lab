within PLA_PET_Recycler.Components;
model Dancer
  parameter Real J=0.004;
  input Real lineTension;
  output Real angle(start=0.35,fixed=true);
  Real angularVelocity(start=0,fixed=true);
equation
  der(angle)=angularVelocity;
  J*der(angularVelocity)=0.105*lineTension-0.6*(angle-0.35)-0.08*angularVelocity;
end Dancer;
