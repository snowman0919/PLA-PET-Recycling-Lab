within PLA_PET_Recycler.Scenarios;
model MOSFETStuckOn
  extends Systems.ThermalExtruderSystem(material=1,stuckOnZone=2);
  parameter String protectedRequirement="SYS-THERM-FAULT-01";
  parameter String estimatedParameters="zone-2 MOSFET short";
  parameter String acceptance="temperature remains below 300 C, or the independent fuse latches open and removes heater power";
end MOSFETStuckOn;
