within PLA_PET_Recycler.Scenarios;
model ExtruderNominalPET
  extends Systems.ThermalExtruderSystem(material=2,targetRPM=16,bulkDensity=380);
  parameter String protectedRequirement="SYS-FLOW-01, SYS-THERM-01";
  parameter String estimatedParameters="PET bulk density, fill and viscosity factor";
  parameter String acceptance="ready state yields positive net flow and <=360 W heater power";
end ExtruderNominalPET;
