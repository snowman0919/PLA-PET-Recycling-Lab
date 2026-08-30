within PLA_PET_Recycler.Components;
model LossyGearbox
  parameter Real ratio=47;
  parameter Real efficiency=0.71 "rated-point screening; REFERENCE_ESTIMATE";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a motorSide;
  Modelica.Mechanics.Rotational.Interfaces.Flange_b outputSide;
  Real inputPower;
  Real outputPower;
  Real lossPower;
equation
  outputSide.phi=motorSide.phi/ratio;
  ratio*efficiency*motorSide.tau+outputSide.tau=0;
  inputPower=motorSide.tau*der(motorSide.phi);
  outputPower=outputSide.tau*der(outputSide.phi);
  lossPower=max(0,abs(inputPower)-abs(outputPower));
end LossyGearbox;

