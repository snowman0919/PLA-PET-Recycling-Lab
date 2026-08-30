within PLA_PET_Recycler.Scenarios;
model DiameterPullerDisturbance
  extends Systems.FilamentFormingSystem(material=1,fanPercent=100,pullerDisturbanceTime=20,pullerDisturbanceFraction=0.04);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end DiameterPullerDisturbance;
