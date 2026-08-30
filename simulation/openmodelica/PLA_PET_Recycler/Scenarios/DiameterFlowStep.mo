within PLA_PET_Recycler.Scenarios;
model DiameterFlowStep
  extends Systems.FilamentFormingSystem(material=1,fanPercent=100,flowStepTime=20,flowStepFraction=0.04);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end DiameterFlowStep;
