within PLA_PET_Recycler.Scenarios;
model PLAFormingNominal
  extends Systems.FilamentFormingSystem(material=1,fanPercent=100);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end PLAFormingNominal;
