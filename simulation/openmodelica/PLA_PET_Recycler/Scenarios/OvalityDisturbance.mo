within PLA_PET_Recycler.Scenarios;
model OvalityDisturbance
  extends Systems.FilamentFormingSystem(material=1,ovalityDisturbance=0.04);
equation
  massFlowGPH=99.4;
  dieOutletTemperature=200;
  enabled=true;
end OvalityDisturbance;
