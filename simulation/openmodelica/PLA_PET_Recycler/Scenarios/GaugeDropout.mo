within PLA_PET_Recycler.Scenarios;
model GaugeDropout
  extends Systems.FilamentFormingSystem(material=1,gaugeDropoutTime=35,gaugeDropoutDuration=1);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end GaugeDropout;
