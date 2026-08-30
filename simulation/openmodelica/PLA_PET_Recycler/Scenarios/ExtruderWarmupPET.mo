within PLA_PET_Recycler.Scenarios;
model ExtruderWarmupPET
  extends Systems.ThermalExtruderSystem(material=2,bulkDensity=380);
  parameter String protectedRequirement="SYS-THERM-01";
  parameter String estimatedParameters="PET thermal profile and four lumped masses";
  parameter String acceptance="all zones reach PET target band without 300 C fuse trip";
end ExtruderWarmupPET;
