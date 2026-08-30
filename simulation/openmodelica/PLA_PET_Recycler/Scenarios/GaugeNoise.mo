within PLA_PET_Recycler.Scenarios;
model GaugeNoise
  extends Systems.FilamentFormingSystem(material=1,gaugeNoiseAmplitude=0.012);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end GaugeNoise;
