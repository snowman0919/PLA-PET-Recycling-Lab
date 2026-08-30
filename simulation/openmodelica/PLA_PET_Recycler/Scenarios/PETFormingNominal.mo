within PLA_PET_Recycler.Scenarios;
model PETFormingNominal
  extends Systems.FilamentFormingSystem(material=2,fanPercent=100);
equation
  massFlowGPH=97.5;
  dieOutletTemperature=265;
  enabled=true;
end PETFormingNominal;
