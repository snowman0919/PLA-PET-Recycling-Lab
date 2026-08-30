within PLA_PET_Recycler.Scenarios;
model PETFormingHighFlow
  extends Systems.FilamentFormingSystem(material=2,fanPercent=100);
equation
  massFlowGPH=200;
  dieOutletTemperature=265;
  enabled=true;
end PETFormingHighFlow;
