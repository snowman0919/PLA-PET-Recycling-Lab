within PLA_PET_Recycler.Scenarios;
model GaugeDropout
  extends Systems.FilamentFormingSystem(material=1,gaugeDropoutTime=20,gaugeDropoutDuration=10);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end GaugeDropout;
