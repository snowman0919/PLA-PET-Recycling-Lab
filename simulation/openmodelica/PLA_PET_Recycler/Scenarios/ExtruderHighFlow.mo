within PLA_PET_Recycler.Scenarios;
model ExtruderHighFlow
  extends Systems.ThermalExtruderSystem(material=1,targetRPM=28,fillFactor=0.30);
  parameter String protectedRequirement="SYS-FLOW-01, SYS-POWER-01";
  parameter String estimatedParameters="upper fill factor and 28 rpm stretch point";
  parameter String acceptance="thermal power and net flow remain finite; 200 g/h remains labelled stretch";
end ExtruderHighFlow;
