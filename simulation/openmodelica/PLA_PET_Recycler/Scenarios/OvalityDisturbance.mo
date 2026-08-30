within PLA_PET_Recycler.Scenarios;
model OvalityDisturbance
  extends Systems.FilamentFormingSystem(material=1,ovalityDisturbance=0.04,ovalityDisturbanceTime=35);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end OvalityDisturbance;
