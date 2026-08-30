within PLA_PET_Recycler.Scenarios;
model HeaterOpen
  extends Systems.ThermalExtruderSystem(material=2,heaterOpenZone=2);
  parameter String protectedRequirement="SYS-THERM-FAULT-01";
  parameter String estimatedParameters="zone-2 open circuit";
  parameter String acceptance="zone-2 power is zero and ready never asserts falsely";
end HeaterOpen;
