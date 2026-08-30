within PLA_PET_Recycler.Scenarios;
model PLAFormingHighFlow
  extends Systems.FilamentFormingSystem(material=1,fanPercent=100);
equation
  massFlowGPH=200;
  dieOutletTemperature=200;
  enabled=true;
end PLAFormingHighFlow;
