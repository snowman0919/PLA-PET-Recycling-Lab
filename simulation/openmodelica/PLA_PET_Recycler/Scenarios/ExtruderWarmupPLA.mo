within PLA_PET_Recycler.Scenarios;
model ExtruderWarmupPLA
  extends Systems.ThermalExtruderSystem(material=1);
  parameter String protectedRequirement="SYS-THERM-01";
  parameter String estimatedParameters="four lumped thermal masses and ambient losses";
  parameter String acceptance="all zones reach PLA target band without 300 C fuse trip";
end ExtruderWarmupPLA;
