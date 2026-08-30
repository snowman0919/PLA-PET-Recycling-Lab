within PLA_PET_Recycler.Scenarios;
model ExtruderNominalPLA
  extends Systems.ThermalExtruderSystem(material=1,targetRPM=16);
  parameter String protectedRequirement="SYS-FLOW-01, SYS-THERM-01";
  parameter String estimatedParameters="bulk density, fill factor, melt/backflow surrogate";
  parameter String acceptance="ready state yields positive net flow and <=360 W heater power";
end ExtruderNominalPLA;
