within PLA_PET_Recycler.Components;
model InputTorqueFuse
  parameter Real reliefTorque = Parameters.inputFuseTorque;
  input Real requestedTorque;
  output Real transmittedTorque;
  output Boolean operating;
equation
  operating = abs(requestedTorque)>=reliefTorque;
  transmittedTorque = max(-reliefTorque,min(reliefTorque,requestedTorque));
end InputTorqueFuse;
