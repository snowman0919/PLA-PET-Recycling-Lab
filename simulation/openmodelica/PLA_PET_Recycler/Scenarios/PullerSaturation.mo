within PLA_PET_Recycler.Scenarios;
model PullerSaturation
  extends Systems.FilamentFormingSystem(material=1,pullerSaturation=0.010,pullerSaturationTime=35,flowStepTime=35,flowStepFraction=0.25);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end PullerSaturation;
