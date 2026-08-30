within PLA_PET_Recycler.Scenarios;
model PullerSlip
  extends Systems.FilamentFormingSystem(material=1,rollerSlipFraction=0.08);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end PullerSlip;
