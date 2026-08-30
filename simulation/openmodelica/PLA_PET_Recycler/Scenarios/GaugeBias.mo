within PLA_PET_Recycler.Scenarios;
model GaugeBias
  extends Systems.FilamentFormingSystem(material=1,gaugeBias=0.02);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end GaugeBias;
